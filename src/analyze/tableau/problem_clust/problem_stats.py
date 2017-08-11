import json
import pandas as pd


class Problem:

    def __init__(self, p_name, topic):
        self.name = p_name
        self.topic = topic
        self.recs = {}  # e.g.{user1: {"correct": {2: 15, 4: 5}, "wrong": {1: 20}, "skip":{3: 2}}, user2: {...}}
        self.TotalUser = 0
        self.TotalComplete = 0
        self.TotalSkip = 0
        self.TotalCompleteDuration = 0
        self.TotalSkipDuration = 0

    def update_p(self, u_name, is_complete, is_correct, attempt_count, duration):
        if u_name not in self.recs:
            self.TotalUser += 1
            self.recs[u_name] = {"correct": {},
                                 "wrong": {},
                                 "skip": {}}
        if is_complete:
            self.TotalComplete += 1
            self.TotalCompleteDuration += duration
            if is_correct:
                self.recs[u_name]["correct"][attempt_count] = duration
            else:
                self.recs[u_name]["wrong"][attempt_count] = duration
        else:
            self.TotalSkip += 1
            self.TotalSkipDuration += duration
            self.recs[u_name]["skip"][attempt_count] = duration

    def cal_AvgComplete(self):
        try:
            x = self.TotalComplete / self.TotalUser
        except:
            x = -1.0
        return x

    def cal_AvgSkip(self):
        try:
            x = self.TotalSkip / self.TotalUser
        except:
            x = -1.0
        return x

    def cal_AvgCompleteDuration(self):
        try:
            x = self.TotalCompleteDuration / self.TotalComplete
        except:
            x = -1.0
        return x

    def cal_AvgSkipDuration(self):
        try:
            x = self.TotalSkipDuration / self.TotalSkip
        except:
            x = -1.0
        return x

    def cal_FirstCompleteCorrectPercent(self):
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

    def cal_AvgAttemptUntilCorrect(self):
        tot_attempt_until_correct = 0
        tot_user = 0
        for i in self.recs:
            correct = self.recs[i]["correct"]
            if len(correct) > 0:
                tot_user += 1
                tot_attempt_until_correct += min(correct.keys())
        try:
            x = tot_attempt_until_correct / tot_user
        except:
            x = -1.0
        return x

    def cal_AvgDurationUntilCorrect(self):
        tot_duration_until_correct = 0
        tot_user = 0
        for i in self.recs:
            correct = self.recs[i]["correct"]
            wrong = self.recs[i]["wrong"]
            skip = self.recs[i]["skip"]
            if len(correct) > 0:
                tot_user += 1
                attempt_num = min(correct.keys())
                all_rec = correct.copy()
                all_rec.update(wrong)
                all_rec.update(skip)
                for j in all_rec:
                    if j <= attempt_num:
                        tot_duration_until_correct += all_rec[j]
        try:
            x = tot_duration_until_correct / tot_user
        except:
            x = -1.0
        return x


def read_file(f_name):
# read json data into problems dictionary {p_name: p_obj}

    global problems
    problems = {}

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
        topic = rec['object']['isPartOf']['name']
        u_name = rec['actor']['name']
        attempt_count = int(rec['generated']['attempt']['count'])
        duration = int(''.join([i for i in rec['generated']['attempt']['duration'] if i.isdigit()]))

        if p_name not in problems:
            problems[p_name] = Problem(p_name, topic)
        problems[p_name].update_p(u_name, is_complete, is_correct, attempt_count, duration)

    f.close()

def get_df():
    my_ls = []
    idxes = problems.keys()
    for i in idxes:
        p = problems[i]
        my_ls.append([p.topic, p.TotalUser, p.TotalComplete, p.TotalSkip,
                      p.cal_AvgComplete(), p.cal_AvgSkip(), p.cal_AvgCompleteDuration(),
                      p.cal_AvgSkipDuration(), p.cal_FirstCompleteCorrectPercent(),
                      p.cal_AvgAttemptUntilCorrect(), p.cal_AvgDurationUntilCorrect()])
    return pd.DataFrame(my_ls,
                        index=idxes,
                        columns=['Topic', 'TotalUser', 'TotalComplete', 'TotalSkip',
                                 'AvgComplete', 'AvgSkip', 'AvgCompleteDuration',
                                 'AvgSkipDuration', 'FirstCompleteCorrectPercent',
                                 'AvgAttemptUntilCorrect', 'AvgDurationUntilCorrect'])


def main():
    read_file('phy140.json')
    data = get_df()
    data.to_csv('phy140_problem_stats.csv')


if __name__ == "__main__":
    main()
