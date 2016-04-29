import pickle
import sonnet as snt


with open("unrated_batch_01.pickle", "r") as f:
	all_sonnets = pickle.load(f)

rated_sonnets = []
for sonnet in all_sonnets:
	for section in sonnet.sections:
		print section.text
		section.get_user_rating()
	rated_sonnets.append(sonnet)

with open("rated_batch_01.pickle", "wb") as f:
	pickle.dump(rated_sonnets, f)