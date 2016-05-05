import pickle
from tensorflow.contrib import skflow
import numpy as np
import tensorflow as tf
import sklearn
import glob



### Load training data
rated_batches = glob.glob("rated*.pickle")
rated_sonnets = []

for batch in rated_batches:
    with open("rated_batch_01.pickle", "r") as f:
        rated_sonnets.extend(pickle.load(f))


cv = skflow.preprocessing.categorical_vocabulary.CategoricalVocabulary()
#Chosen because of sparse nature of data, but don't want to use the
#full vocab tokenizer because I want to treat the templates as a block.

def convert_to_sequence(section):
    sequence = []
    for template, line in zip(section.template_list, section.lines):
        sequence.append(template.raw_text)
        for choice in line.choices:
            sequence.append(choice)
    return sequence

def bin_rating(rating, low_break, high_break):
    if rating < low_break:
        return "low"
    elif rating < high_break:
        return "moderate"
    else:
        return "high"

seqs = [convert_to_sequence(section) for sonnet in rated_sonnets for section in sonnet.sections]
human_score_cat = [bin_rating(section.human, 4, 6) for sonnet in rated_sonnets for section in sonnet.sections]
interest_score_cat = [bin_rating(section.interesting, 4, 7) for sonnet in rated_sonnets for section in sonnet.sections]
offense_score_cat = [bin_rating(section.offensive, 1, 4) for sonnet in rated_sonnets for section in sonnet.sections]


for seq in seqs:
    for item in seq:
        cv.add(item)
cv.freeze()

n_words = len(cv._mapping)
MAX_SEQUENCE_LENGTH = max([len(seq) for seq in seqs])

#Make each seq into a vector of indexes
def transform(seqs):
    for seq in seqs:
        choice_ids = np.zeros(MAX_SEQUENCE_LENGTH, np.int64)
        for index, choice in enumerate(seq):
            if index >= MAX_SEQUENCE_LENGTH:
                break
            choice_ids[index] = cv.get(choice)
        yield(choice_ids)

X = np.array(list(transform(seqs)))


def prepare_rating_cats(binned_ratings):
    cv_y = skflow.preprocessing.categorical_vocabulary.CategoricalVocabulary()
    for row in binned_ratings:
        cv_y.add(row)
    cv_y.freeze()

    def transform_cat(cat):
        for rating in cat:
            yield (cv_y.get(rating))

    y = np.array(list(transform_cat(binned_ratings)))
    return y

y = prepare_rating_cats(interest_score_cat)
X_train, X_test, y_train, y_test = sklearn.cross_validation.train_test_split(X, y, test_size = 0.2, random_state = 1)

EMBEDDING_SIZE = 50


def rnn_model(X, y):
    "Recurrent neural network to predict from sequence of templates/choices to a class"
    #Create embedding matrix of size [n_words, EMBEDDING_SIZE] then maps word indexes of the sequence
    #into [batch_size, sequence_length, EMBEDDING_SIZE]
    choice_vectors = skflow.ops.categorical_variable(X, n_classes = n_words, embedding_size = EMBEDDING_SIZE, name = "choices")
    #Split into list of embedding per choice, removing seq length dim
    #Result is a list of tensors [batch_size, EMBEDDING_SIZE]
    choice_list = skflow.ops.split_squeeze(1, MAX_SEQUENCE_LENGTH, choice_vectors)
    #Create Gated Recurrent Unit cell with hidden size EMBEDDING_SIZE
    cell = tf.nn.rnn_cell.GRUCell(EMBEDDING_SIZE)
    #Create the network to length MAX_SEQUENCE_LENGTH and pass choice_list to each unit
    _, encoding = tf.nn.rnn(cell, choice_list, dtype = tf.float32)
    #Use encoding of last step and pass it a features for logistic regression
    #over output classes
    return skflow.models.logistic_regression(encoding, y)

classifier = skflow.TensorFlowEstimator(model_fn = rnn_model, n_classes = 4, steps = 1000, optimizer = "Adam",
    learning_rate = 0.01, continue_training = True)

while True:
    classifier.fit(X_train, y_train, logdir = '/tmp/snt_model')
    score = sklearn.metrics.accuracy_score(y_test, classifier.predict(X_test))
    print("Accuracy: {0:f}".format(score))

classifier.save("models/interest_classifier_20160506")
