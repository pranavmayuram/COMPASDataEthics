import cmd
import sys
import os
import csv
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
matplotlib.style.use('ggplot')
import pandas as pd
from pandas import DataFrame, Series

class CSVReaderConst(object):
    HIGHEST_RISK = 10
    LOWEST_RISK = 1
    RACES_TO_CORRECT = ["African American", "White"]
    RECIDIVISM_COL_NAME = "two_year_recid"

class DataAnalyzer(object):
    def __init__(self, filepath_in):
        self.plot_filepath = filepath_in
        self.df = pd.read_csv(filepath_in)

    def trait_breakdown(self, col_name):
        breakdown = self.df[col_name.lower()].value_counts(sort=True, ascending=False)
        print(breakdown)
        return breakdown

    def plot_recid(self, col_name, attr, recid_dec_col_name):
        # cuts down table to only where attr exists, creates 2D table using decile, and actual recidivism occuring
        updated_df = self.df[self.df[col_name] == attr]
        recid_table = pd.crosstab(index=updated_df[recid_dec_col_name.lower()],
                                  columns=updated_df[CSVReaderConst.RECIDIVISM_COL_NAME])
        recid_table.plot(kind="bar",
                         figsize=(8, 8),
                         stacked=True,
                         title="{0!s}, {1!s} = {2!s}".format(recid_dec_col_name.capitalize(),
                                                             col_name.capitalize(),
                                                             attr.capitalize()))
        plt.draw()
        plt.pause(0.001)

    def get_trait_key(self, trait, score):
        return "{0!s}_{1!s}".format(trait, score)

    def correct_for(self, col_name, recid_dec_col_name, traits=[]):
        '''
        Across same col_name, correct the attribute for each trait to remove bias
        '''
        if traits == []:
            trait_dict = self.trait_breakdown(col_name=col_name)
            for trait, percentage in trait_dict.iteritems():
                traits.append(trait)

        print(traits)
        baseline_error_dict = {}
        baseline_abs_error_dict = {}
        people_per_trait = {}
        baseline_bias_dict = {}
        for trait in traits:
            group = self.df[self.df[col_name] == trait]
            # print(group)
            num_members = len(group)
            for index, person in group.iterrows():
                trait_key = self.get_trait_key(trait, int(person[recid_dec_col_name]))
                if int(person[CSVReaderConst.RECIDIVISM_COL_NAME]) == 1:
                    person_error = float(person[recid_dec_col_name]) - CSVReaderConst.HIGHEST_RISK
                else:
                    person_error = float(person[recid_dec_col_name]) - CSVReaderConst.LOWEST_RISK
                if baseline_error_dict.get(trait_key, None) is None:
                    baseline_error_dict[trait_key] = person_error
                    baseline_abs_error_dict[trait_key] = abs(person_error)
                    people_per_trait[trait_key] = 1
                else:
                    baseline_error_dict[trait_key] += person_error
                    baseline_abs_error_dict[trait_key] += abs(person_error)
                    people_per_trait[trait_key] += 1
            if num_members == 0:
                raise ValueError("No members found in group {0!s}".format(trait))

        for trait_key, error in baseline_error_dict.items():
            baseline_bias_dict[trait_key] = error/people_per_trait[trait_key]
            # print(total_error)
            print("For group {0!s}, baseline error: {1:.3f}, baseline bias: {2:.3f}".format(trait_key,
                                                                                            baseline_error_dict[trait_key],
                                                                                            baseline_bias_dict[trait_key]))

        print("=========================================")
        new_error_dict = {}
        new_abs_error_dict = {}
        new_bias_dict = {}
        for trait in traits:
            group = self.df[self.df[col_name] == trait]
            # print(group)
            num_members = len(group)
            for index, person in group.iterrows():
                trait_key = self.get_trait_key(trait, int(person[recid_dec_col_name]))
                if int(person[CSVReaderConst.RECIDIVISM_COL_NAME]) == 1:
                    person_error = float(person[recid_dec_col_name]) - CSVReaderConst.HIGHEST_RISK
                else:
                    person_error = float(person[recid_dec_col_name]) - CSVReaderConst.LOWEST_RISK
                if new_error_dict.get(trait_key, None) is None:
                    new_error_dict[trait_key] = person_error
                    new_abs_error_dict[trait_key] = abs(person_error)
                    people_per_trait[trait_key] = 1
                else:
                    new_error_dict[trait_key] += person_error
                    new_abs_error_dict[trait_key] += abs(person_error)
                    people_per_trait[trait_key] += 1
            if num_members == 0:
                raise ValueError("No members found in group {0!s}".format(trait))

        for trait_key, error in new_error_dict.items():
            new_bias_dict[trait_key] = error/people_per_trait[trait_key]
            # print(total_error)
            print("For group {0!s}, new baseline error: {1:.3f}, new baseline bias: {2:.3f}".format(trait_key,
                                                                                                    new_error_dict[trait_key],
                                                                                                    new_bias_dict[trait_key]))
        return baseline_error_dict, baseline_bias_dict, new_error_dict


class AnalyzerShell(cmd.Cmd):
    intro = 'Welcome to the analyzer shell. Type help or ? to list commands.\n'
    prompt = '(analyzer) '
    def setup(self, file_path):
        self.data_analyzer = DataAnalyzer(file_path)

    def do_trait_breakdown(self, arg):
        'Get a percentage and count breakdown of specified argument'
        self.data_analyzer.trait_breakdown(col_name=arg)

    def do_plot_recid(self, arg):
        'Plot the value of recidivism decile, with a stacked chart of how many actually had recidivism for this attribute.\n \
        i.e. plot_recid race Caucasian decile_score'
        split_up = arg.split(" ")
        self.data_analyzer.plot_recid(*split_up)

    def do_correct_for(self, arg):
        'Correct a particular decile score attribute based on a specific column.\nSpecificy traits in the column to correct, or "ALL" for an analysis of all. \
         \ni.e. correct_for decile_score race African-American, Caucasian OR correct_for decile_score race ALL'
        split_up = arg.split(" ", 2)
        # print(split_up)
        dec_name = split_up[0]
        col_name = split_up[1]
        traits = split_up[2].split(", ")
        if (traits[0] == "ALL"):
            traits = []
        self.data_analyzer.correct_for(col_name=col_name, recid_dec_col_name=dec_name, traits=traits)

    def do_quit(self, arg):
        'Quit'
        print('Thank you for using analyzer')
        return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Need filepath")
    else:
        shell = AnalyzerShell()
        shell.setup(os.path.normpath(sys.argv[1]))
        shell.cmdloop()