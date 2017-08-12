import json
import pandas as pd
from matplotlib import pyplot as plt
from sklearn import preprocessing
from scipy.cluster.hierarchy import dendrogram, linkage, to_tree
from scipy.cluster.hierarchy import cophenet
from scipy.spatial.distance import pdist
from functools import reduce


class User:

    def __init__(self, uniqname):
        self.uniqname = uniqname
        self.recs = {}  # e.g.{problem1: {"correct": {2: 15, 4: 5}, "wrong": {1: 20}, "skip": {3: 2}, problem2: {...}}
        self.TotalProblem = 0
        self.TotalComplete = 0
        self.TotalSkip = 0
        self.TotalCompleteDuration = 0
        self.TotalSkipDuration = 0

    def update_u(self, p_name, is_complete, is_correct, attempt_count, duration):
        if p_name not in self.recs:
            self.TotalProblem += 1
            self.recs[p_name] = {"correct": {},
                                 "wrong": {},
                                 "skip": {}}
        if is_complete:
            self.TotalComplete += 1
            self.TotalCompleteDuration += duration
            if is_correct:
                self.recs[p_name]["correct"][attempt_count] = duration
            else:
                self.recs[p_name]["wrong"][attempt_count] = duration
        else:
            self.TotalSkip += 1
            self.TotalSkipDuration += duration
            self.recs[p_name]["skip"][attempt_count] = duration

    def get_TotalProblem(self):
        return self.TotalProblem

    def get_SkippedPercent(self):
        SkippedProblem = 0
        for i in self.recs:
            correct = self.recs[i]["correct"]
            wrong = self.recs[i]["wrong"]
            if len(correct.keys()) + len(wrong.keys()) == 0:
                SkippedProblem += 1
        return SkippedProblem / self.TotalProblem

    def get_SolvedPercent(self):
        SolvedProblem = 0
        for i in self.recs:
            correct = self.recs[i]["correct"]
            if len(correct) > 0:
                SolvedProblem += 1
        return SolvedProblem / self.TotalProblem

    def get_UnsolvedPercent(self):
        return 1 - self.get_SolvedPercent() - self.get_SkippedPercent()

    def get_SkipRate(self):
        return self.TotalSkip / (self.TotalSkip + self.TotalComplete)

    def get_AvgCompleteDuration(self):
        try:
            x = self.TotalCompleteDuration / self.TotalComplete
        except:
            x = -1.0
        return x

    def get_AvgSkipDuration(self):
        try:
            x = self.TotalSkipDuration / self.TotalSkip
        except:
            x = -1.0
        return x

    def get_FirstCompleteCorrectPercent(self):
        tot_first_complete = 0
        tot_first_complete_correct = 0
        for i in self.recs:
            correct = self.recs[i]["correct"]
            wrong = self.recs[i]["wrong"]
            if len(correct.keys()) + len(wrong.keys()) > 0:
                tot_first_complete += 1
                if min(list(correct.keys()) + list(wrong.keys())) in correct:
                    tot_first_complete_correct += 1
        try:
            x = tot_first_complete_correct / tot_first_complete
        except:
            x = -1.0
        return x

    def get_AvgAttemptUntilCorrect(self):
        tot_attempt_until_correct = 0
        tot_problem = 0
        for i in self.recs:
            correct = self.recs[i]["correct"]
            if len(correct) > 0:
                tot_problem += 1
                tot_attempt_until_correct += min(correct.keys())
        try:
            x = tot_attempt_until_correct / tot_problem
        except:
            x = -1.0
        return x

    def get_AvgDurationUntilCorrect(self):
        tot_duration_until_correct = 0
        tot_problem = 0
        for i in self.recs:
            correct = self.recs[i]["correct"]
            wrong = self.recs[i]["wrong"]
            skip = self.recs[i]["skip"]
            if len(correct) > 0:
                tot_problem += 1
                attempt_num = min(correct.keys())
                all_rec = correct.copy()
                all_rec.update(wrong)
                all_rec.update(skip)
                for j in all_rec:
                    if j <= attempt_num:
                        tot_duration_until_correct += all_rec[j]
        try:
            x = tot_duration_until_correct / tot_problem
        except:
            x = -1.0
        return x

def read_file(f_name):
    # read from json file and get pandas data frame

    global users
    users = {}

    f = open(f_name, 'r')
    for line in f:
        rec = json.loads(line)

        # use only Completed & Skipped event records
        if 'Completed' in rec['action']:
            is_complete = True
            if rec['generated']['extensions']['isStudentAnswerCorrect'] == 'true':
                is_correct = True
            else:
                is_correct = False
        elif 'Skipped' in rec['action']:
            is_complete = False
            is_correct = None
        else:
            continue
        p_name = rec['object']['name']
        uniqname = rec['actor']['name']
        attempt_count = int(rec['generated']['attempt']['count'])
        duration = int(''.join([i for i in rec['generated']['attempt']['duration'] if i.isdigit()]))

        if uniqname not in users:
            users[uniqname] = User(uniqname)
        users[uniqname].update_u(p_name, is_complete, is_correct, attempt_count, duration)

    f.close()

def get_df():
    global hclust_vars
    hclust_vars = ['TotalProblem',
                   'SolvedPercent',
                   'UnsolvedPercent',
                   'SkippedPercent',
                   'SkipRate',
                   'AvgCompleteDuration',
                   'AvgSkipDuration',
                   'FirstCompleteCorrectPercent',
                   'AvgAttemptUntilCorrect',
                   'AvgDurationUntilCorrect']
    my_ls = []
    idxes = users.keys()
    for i in idxes:
        p = users[i]
        my_ls.append([p.get_TotalProblem(),
                      p.get_SolvedPercent(),
                      p.get_UnsolvedPercent(),
                      p.get_SkippedPercent(),
                      p.get_SkipRate(),
                      p.get_AvgCompleteDuration(),
                      p.get_AvgSkipDuration(),
                      p.get_FirstCompleteCorrectPercent(),
                      p.get_AvgAttemptUntilCorrect(),
                      p.get_AvgDurationUntilCorrect()])
    return pd.DataFrame(my_ls,
                        index=idxes,
                        columns=hclust_vars)


read_file('phy140.json')
data = get_df()
data.to_csv('phy140_user_stats.csv')


## hierarchical clustering

# data standardization
min_max_scaler = preprocessing.MinMaxScaler()
idxes = users.keys()
data_scaled = pd.DataFrame(min_max_scaler.fit_transform(data),
                           index=idxes,
                           columns=hclust_vars)

# hclust
# linkage() function will use the method and metric you picked to calculate the distances of the clusters
# method: ward; metric: euclidean (default)
Z = linkage(data_scaled, method='ward')
# Z[i] will tell us which clusters were merged in the i-th iteration,
# each row of the resulting array has the format [idx1, idx2, dist, sample_count]
T = to_tree(Z, rd=False)

# check performance of hclust
# The closer c is to 1 the better the clustering preserves the original distances
c, coph_dists = cophenet(Z, pdist(data_scaled))
print("c value: " + str(c))



def add_node(node, parent):
    # create new node and append it to its parent's children
    newNode = dict(node_id=node.id, children=[])
    parent["children"].append(newNode)
    # add the current node's children
    if node.left: add_node(node.left, newNode)
    if node.right: add_node(node.right, newNode)

def label_tree(n):
    # If the node is a leaf, then we have its name and statistics
    if len(n["children"]) == 0:
        leafNames = [ id2name[n["node_id"]] ]
        n["name"] = leafNames[0]
        n["TotalProblem"] = users[n["name"]].get_TotalProblem()
        n["SolvedPercent"] = users[n["name"]].get_SolvedPercent()
        n["UnsolvedPercent"] = users[n["name"]].get_UnsolvedPercent()
        n["SkippedPercent"] = users[n["name"]].get_SkippedPercent()
        n["SkipRate"] = users[n["name"]].get_SkipRate()
        n["AvgCompleteDuration"] = users[n["name"]].get_AvgCompleteDuration()
        n["AvgSkipDuration"] = users[n["name"]].get_AvgSkipDuration()
        n["FirstCompleteCorrectPercent"] = users[n["name"]].get_FirstCompleteCorrectPercent()
        n["AvgAttemptUntilCorrect"] = users[n["name"]].get_AvgAttemptUntilCorrect()
        n["AvgDurationUntilCorrect"] = users[n["name"]].get_AvgDurationUntilCorrect()

    # If not, flatten all the leaves in the node's subtree
    else:
        leafNames = reduce(lambda ls, c: ls + label_tree(c), n["children"], [])
        n["name"] = ''

    # Delete the node id since we don't need it anymore and it makes for cleaner JSON
    del n["node_id"]

    return leafNames


d3_dendro = dict(name='users', children=[])
add_node(T, d3_dendro)
id2name = dict(zip(range(len(idxes)), idxes))
label_tree(d3_dendro["children"][0])
json.dump(d3_dendro, open("d3-dendrogram-phy140.json", "w"), sort_keys=True, indent=4)



# show full dendrogram
plt.figure(figsize=(25, 8))
plt.title('Hierarchical Clustering Dendrogram')
plt.xlabel('users')
plt.ylabel('distance')
dendrogram(
    Z,
    leaf_rotation=90,  # rotates the x axis labels
    labels=data_scaled.index,
    leaf_font_size=8,  # font size for the x axis labels
)
plt.show()




