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
        error_vals = []
        for threshold in sorted(threshold_res.iterkeys()):
            val_dict = threshold_res[threshold]
            x_coords.append(val_dict["false_pos"])
            y_coords.append(val_dict["false_neg"])
            colors.append(default_color)
            error_vals.append(val_dict["error"])
            error_labels.append(" {0!s} (error={1!s}, bias={2:.3f})".format(threshold, val_dict["error"], val_dict["bias"]))
            
        # change color for lowest error producing threshold
        colors[error_vals.index(min(error_vals))] = lowest_error_color
        
        fig = plt.figure()
        plt.scatter(x_coords, y_coords, c=colors)
        plt.xlabel("False Positives")
        plt.ylabel("False Negatives")
        for idx, label in enumerate(error_labels):
            plt.annotate(label, (x_coords[idx], y_coords[idx]))
        # plt.plot(np.unique(x_coords), np.poly1d(np.polyfit(x_coords, y_coords, 1))(np.unique(x_coords)))
        plt.draw()
        plt.title("Threshold Plot {0!s}\n{1!s} = {2!s}".format(recid_dec_col_name, 
                                                               col_name.capitalize(), 
                                                               trait))
        plt.pause(0.001)


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
