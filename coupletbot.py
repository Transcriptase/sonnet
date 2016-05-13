import sonnet as snt
from tensorflow.contrib import skflow
import model
import numpy as np
import logging
from secrets import *
import tweepy
import pickle
import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("Loading humanity model...")
hum_classifier = skflow.TensorFlowEstimator.restore("models/human_classifier_20160510")
logging.info("Done.")
logging.info("Loading interest model...")
int_classifier = skflow.TensorFlowEstimator.restore("models/interest_classifier_20160510")
logging.info("Done.")

HUMAN_REV_MAPPING = ['<UNK>', 'low', 'moderate', 'high']
INTEREST_REV_MAPPING = ['<UNK>', 'low', 'moderate', 'high']

vocab = snt.Vocab()
sw = snt.SonnetWriter(vocab)
sw.load_templates("line_templates.csv")

vocab.add_random_collections(2)
couplets = snt.HeroicCouplets(12)

sw.new_poem(couplets)

seqs  = [model.convert_to_sequence(section) for section in couplets.sections]
X = np.array(list(model.transform(seqs)))

def sum_ratings(probs):
    return sum([prob * rating for prob, rating in zip(probs, range(4))])

hum_ratings = [sum_ratings(probs) * 3 for probs in hum_classifier.predict_proba(X)]
int_ratings = [sum_ratings(probs) * 3 for probs in int_classifier.predict_proba(X)]

for section, hum_rat, int_rat in zip(couplets.sections, hum_ratings, int_ratings):
    section.human = hum_rat
    section.interesting = int_rat

couplets.sections.sort(key= lambda x: x.human*x.interesting)

timestamp = datetime.now()
pickle.dump(couplets, "unrated_couplets_batch_().pickle".format(timestamp.strftime("%Y%m%d-%H%M")))

auth = tweepy.OAuthHandler(C_KEY, C_SECRET)
auth.set_access_token(A_TOKEN, A_TOKEN_SECRET)
api = tweepy.API(auth)


NUM_TO_TWEET = 4

for couplet in couplets.sections[-NUM_TO_TWEET]:
    api.update_status(couplet.text)