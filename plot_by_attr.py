import cmd
import sys
import os
import csv
import math
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
        
    def _get_median(self, some_list):
        if len(some_list) is 0:
            return None
        elif len(some_list) % 2 is 1:
            return some_list[len(some_list)/2]
        else:
            return float(some_list[len(some_list)/2] + some_list[len(some_list)/2 + 1])/2

    def trait_breakdown(self, col_name):
        '''
        Returns a dictionary of each different trait, and its count within a given column
        '''
        breakdown = self.df[col_name.lower()].value_counts(sort=True, ascending=False)
        print(breakdown)
        return breakdown

    def plot_recid(self, col_name, attr, recid_dec_col_name):
        '''
        Plots the breakdown of those who actually commit recidivism by the recidivism score they received
        '''
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

    def correct_for(self, col_name, recid_dec_col_name, traits=[], rms=False):
        '''
        Across same col_name, correct the attribute for each trait to remove bias
        '''
        if traits == []:
            trait_dict = self.trait_breakdown(col_name=col_name)
            for trait, percentage in trait_dict.iteritems():
                traits.append(trait)

        print(traits)
        baseline_error_dict = {}
        rms_error_dict = {}
        baseline_bias_dict = {}
        
        # for each trait, get some error and bias which can be printed/corrected for
        for trait in traits:
            group = self.df[self.df[col_name] == trait]
            num_members = len(group)
            total_abs_error = 0
            total_error = 0
            total_squared_residuals = 0
            # iterate through each person in group
            for index, person in group.iterrows():
                if int(person[CSVReaderConst.RECIDIVISM_COL_NAME]) == 1:
                    # if recidivism occured, we should expect a high risk, use HIGHEST_RISK
                    person_error = float(person[recid_dec_col_name]) - CSVReaderConst.HIGHEST_RISK
                else:
                    # if recidivism did not occur, we should expect a low risk, use LOWEST_RISK
                    person_error = float(person[recid_dec_col_name]) - CSVReaderConst.LOWEST_RISK
                # compound error (for bias calculation), and absolute error
                total_error += person_error
                total_squared_residuals += pow(person_error, 2)
                total_abs_error += abs(person_error)
            if num_members == 0:
                raise ValueError("No members found in group {0!s}".format(trait))
            baseline_bias = total_error/float(num_members)
            # if mostly over-predicted, baseline bias positive. if under, negative.
            baseline_error_dict[trait] = total_abs_error/float(num_members)
            baseline_bias_dict[trait] = baseline_bias
            rms_error_dict[trait] = math.sqrt(total_squared_residuals/float(num_members))
            if rms:
                print("For group {0!s}, rms error: {1:.3f}, baseline bias: {2:.3f}".format(trait,
                                                                                           rms_error_dict[trait],
                                                                                           baseline_bias_dict[trait]))
            else:
                print("For group {0!s}, baseline error: {1:.3f}, baseline bias: {2:.3f}".format(trait,
                                                                                                baseline_error_dict[trait],
                                                                                                baseline_bias_dict[trait]))

        # bias correction calculation, now that we have bias per demographic (trait)                                                                                
        print("=========================================")
        new_error_dict = {}
        new_rms_error_dict = {}
        new_baseline_dict = {}
        for trait in traits:
            group = self.df[self.df[col_name] == trait]
            num_members = len(group)
            new_total_error = 0
            total_abs_error = 0
            total_squared_residuals = 0
            for index, person in group.iterrows():
                # adjust/correct for bias of this group, subtract per person
                corrected_decile = float(person[recid_dec_col_name]) - float(baseline_bias_dict[trait])
                if int(person[CSVReaderConst.RECIDIVISM_COL_NAME]) == 1:
                    person_error = float(corrected_decile) - CSVReaderConst.HIGHEST_RISK
                else:
                    person_error = float(corrected_decile) - CSVReaderConst.LOWEST_RISK
                new_total_error += person_error
                total_abs_error += abs(person_error)
                total_squared_residuals += pow(person_error, 2)
            if num_members == 0:
                raise ValueError("No members found in group {0!s}".format(trait))
            # bias should turn to 0 every time since we corrected everyone for this
            new_baseline_bias = new_total_error/float(num_members)
            new_error_dict[trait] = total_abs_error/float(num_members)
            new_rms_error_dict[trait] = math.sqrt(total_squared_residuals/float(num_members))
            new_baseline_dict[trait] = new_baseline_bias
            if rms:
                print("For group {0!s}, corrected rms error: {1:.3f}".format(trait, new_rms_error_dict[trait]))
            else:
                print("For group {0!s}, corrected error: {1:.3f}".format(trait, new_error_dict[trait]))

        return baseline_error_dict, rms_error_dict, baseline_bias_dict, new_error_dict, new_rms_error_dict


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

    def do_correct_for(self, arg, calc_rms=False):
        'Correct a particular decile score attribute based on a specific column.\nSpecificy traits in the column to correct, or "ALL" for an analysis of all. \
         \ni.e. correct_for decile_score race African-American, Caucasian OR correct_for decile_score race ALL'
        split_up = arg.split(" ", 2)
        # print(split_up)
        dec_name = split_up[0]
        col_name = split_up[1]
        traits = split_up[2].split(", ")
        if (traits[0] == "ALL"):
            traits = []
        self.data_analyzer.correct_for(col_name=col_name, recid_dec_col_name=dec_name, traits=traits, rms=calc_rms)
    
    def do_correct_for_rms(self, arg):
        'Same as correct_for, but using root mean squared error instead of linear error calculation'
        self.do_correct_for(arg=arg, calc_rms=True)

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