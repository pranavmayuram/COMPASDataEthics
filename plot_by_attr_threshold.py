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
    THRESHOLD_RISK = 4
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
        
    def plot_threshold(self, col_name, trait, recid_dec_col_name):
        threshold_res = {}
        
        # calculate false pos, neg, error, etc. for a group across all possible threshold values
        for threshold in range(1, 10):
            threshold_res[threshold] = {"false_neg": 0, "false_pos": 0, "error": 0, "bias": 0}
            signed_error = 0
            
            frame = self.df
            if trait != "ALL":
                frame = self.df[self.df[col_name] == trait]
                
            for index, person in frame.iterrows():
                person_error = 0
                
                if int(person[CSVReaderConst.RECIDIVISM_COL_NAME]) == 1:
                    if int(person[recid_dec_col_name] <= threshold):
                        person_error = -1
                        threshold_res[threshold]["false_neg"] += 1
                else:
                    if int(person[recid_dec_col_name] > threshold):
                        person_error = 1
                        threshold_res[threshold]["false_pos"] += 1
                        
                threshold_res[threshold]["error"] += abs(person_error)
                signed_error += person_error
                
            threshold_res[threshold]["bias"] = signed_error/float(len(frame))
            print("Stats for {0!s}: {1!s} at threshold {2!s} --> error: {3:.3f}, bias: {4:.3f}".format(col_name,
                                                                                                       trait,
                                                                                                       threshold,
                                                                                                       threshold_res[threshold]["error"],
                                                                                                       threshold_res[threshold]["bias"]))
        print(threshold_res)
        
        # plot out the false pos, neg, error, etc. for this group
        default_color = "blue"
        lowest_error_color = "magenta"
        x_coords = []
        y_coords = []
        colors = []
        error_labels = []
        for threshold, val_dict in threshold_res.items():
            x_coords.append(val_dict["false_pos"])
            y_coords.append(val_dict["false_neg"])
            colors.append(default_color)
            error_labels.append(val_dict["false_pos"] + val_dict["false_neg"])
            
        # change color for lowest error producing threshold
        colors[error_labels.index(min(error_labels))] = lowest_error_color
        
        print(colors)
        
        fig = plt.figure()
        plt.scatter(x_coords, y_coords, c=colors)
        plt.xlabel("False Positives")
        plt.ylabel("False Negatives")
        for idx, label in enumerate(error_labels):
            plt.annotate(label, (x_coords[idx], y_coords[idx]))
        # plt.plot(np.unique(x_coords), np.poly1d(np.polyfit(x_coords, y_coords, 1))(np.unique(x_coords)))
        plt.draw()
        plt.pause(0.001)

    def correct_for(self, col_name, recid_dec_col_name, traits=[]):
        '''
        Across same col_name, correct the attribute for each trait to remove bias
        '''
        if traits == []:
            trait_dict = self.trait_breakdown(col_name=col_name)
            for trait, percentage in trait_dict.iteritems():
                traits.append(trait)

        print(traits)
        threshold_res = {}
        
        for threshold in range(1, 10):
            threshold_res[threshold] = {"false_neg": 0, "false_pos": 0}
            overall_error = 0
            for index, person in self.df.iterrows():
                if int(person[CSVReaderConst.RECIDIVISM_COL_NAME]) == 1:
                    person_error = -1*int(person[recid_dec_col_name] <= threshold)
                else:
                    person_error = int(person[recid_dec_col_name] > threshold)
                overall_error += person_error
            overall_normalized_error = overall_error/float(len(self.df))
            print("Normalized error across all groups at threshold {0!s}: {1:.3f}".format(threshold, overall_normalized_error))

            baseline_error_dict = {}
            baseline_bias_dict = {}
            for trait in traits:
                group = self.df[self.df[col_name] == trait]
                num_members = len(group)
                total_error = 0
                for index, person in group.iterrows():
                    if int(person[CSVReaderConst.RECIDIVISM_COL_NAME]) == 1:
                        person_error = -1*(int(person[recid_dec_col_name] <= threshold))
                    else:
                        person_error = int(person[recid_dec_col_name] > threshold)
                    # don't need abs error because it will always be 0 or 1 (correct or incorrect)
                    total_error += person_error
                if num_members == 0:
                    raise ValueError("No members found in group {0!s}".format(trait))
                # if mostly over-predicted, baseline bias positive. if under, negative.
                baseline_error_dict[trait] = total_error/float(num_members)
                baseline_bias_dict[trait] = baseline_error_dict[trait] - overall_normalized_error
                # print(total_error)
                print("At threshold {3!s} group {0!s}, baseline error: {1:.3f}, baseline bias: {2:.3f}".format(trait,
                                                                                                               baseline_error_dict[trait],
                                                                                                               baseline_bias_dict[trait],
                                                                                                               threshold))
        print("=========================================")
        new_error_dict = {}
        new_baseline_dict = {}
        for trait in traits:
            group = self.df[self.df[col_name] == trait]
            num_members = len(group)
            new_total_error = 0
            for index, person in group.iterrows():
                # compensate for bias of this group, subtract bias*HIGHEST_RISK per person
                # how to improve this, or pick a better multiple? Why is it being subtracted always, it just means wrong!
                corrected_decile = float(person[recid_dec_col_name])
                if int(person[CSVReaderConst.RECIDIVISM_COL_NAME]) == 1:
                    if person[recid_dec_col_name] <= CSVReaderConst.THRESHOLD_RISK:
                        # incorrectly predicted non-recidivism (low risk)
                        corrected_decile = float(person[recid_dec_col_name]) + float(baseline_bias_dict[trait])*CSVReaderConst.HIGHEST_RISK
                else:
                    if corrected_decile > CSVReaderConst.THRESHOLD_RISK:
                        # incorrectly predicted recidivism (high risk)
                        corrected_decile = float(person[recid_dec_col_name]) - float(baseline_bias_dict[trait])*CSVReaderConst.HIGHEST_RISK

                if int(person[CSVReaderConst.RECIDIVISM_COL_NAME]) == 1:
                    person_error = int(corrected_decile <= CSVReaderConst.THRESHOLD_RISK)
                else:
                    person_error = int(corrected_decile > CSVReaderConst.THRESHOLD_RISK)
                new_total_error += person_error
            if num_members == 0:
                raise ValueError("No members found in group {0!s}".format(trait))
            new_error_dict[trait] = new_total_error/float(num_members)
            new_baseline_dict[trait] = new_error_dict[trait] - overall_normalized_error
            print("For group {0!s}, corrected error: {1:.3f}, corrected bias: {2:.3f}".format(trait,
                                                                                              new_error_dict[trait],
                                                                                              new_baseline_dict[trait]))

        return baseline_error_dict, baseline_bias_dict, new_error_dict


class AnalyzerShell(cmd.Cmd):
    intro = 'Welcome to the analyzer shell. Type help or ? to list commands.\n'
    prompt = '(analyzer) '
    def setup(self, file_path):
        self.data_analyzer = DataAnalyzer(file_path)

    def do_trait_breakdown(self, arg):
        'Get a percentage and count breakdown of specified argument'
        self.data_analyzer.trait_breakdown(col_name=arg)

    def do_plot_threshold(self, arg):
        'Plot the value of false positives and negatives, with a line of best fit of degree 2, based on colname and trait provided.\n \
        Using ALL will use all people. i.e. plot_threshold race Caucasian decile_score OR plot_threshold race ALL decile_score'
        split_up = arg.split(" ")
        self.data_analyzer.plot_threshold(*split_up)

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
        print("Need filepath and threshold for decile_score")
    else:
        shell = AnalyzerShell()
        shell.setup(os.path.normpath(sys.argv[1]))
        shell.cmdloop()
