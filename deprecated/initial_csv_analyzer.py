import cmd
import sys
import os
import csv

class CSVReaderConst(object):
    HIGHEST_RISK = 10
    LOWEST_RISK = 1
    RACES_TO_CORRECT = ["African American", "White"]
    RECIDIVISM_COL_NAME = "two_year_recid"

class CSVReader(object):
    '''
    Class to read in CSV file object, and calculate different factors about it.
    '''
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.csv_list = [];

    def read_file(self):
        '''Reads everything from file into csv_list'''
        with open(self.csv_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.csv_list.append(row)

    def trait_breakdown(self, col_name, to_print=False):
        '''Find each trait and the percentage it is of a particular column. Print results, and return dict.'''
        total_def_rows = 0
        trait_dict = {}
        trait_percentage_dict = {}
        for row_dict in self.csv_list:
            if row_dict.get(col_name, None):
                trait = row_dict[col_name]
                if trait in trait_dict:
                    trait_dict[trait] += 1
                else:
                    trait_dict[trait] = 1
                total_def_rows += 1

        if to_print is True:
            print("In column {0!s}, {1!s} total defined rows were found".format(col_name, total_def_rows))

        for trait, num_def_rows in trait_dict.items():
            abundance = num_def_rows/float(total_def_rows)
            trait_percentage_dict[trait] = abundance
            if to_print is True:
                print("{0!s}: {1!s} found, {2:.3f}%".format(trait, num_def_rows, abundance*100))

        return trait_percentage_dict

    def rows_with(self, col_name, traits):
        '''Find all rows with particular property. Return list of rows.'''
        ret_dict = {}
        for trait in traits:
            ret_dict[trait] = []
        for row_dict in self.csv_list:
            if row_dict.get(col_name, None) in traits:
                ret_dict[row_dict[col_name]].append(row_dict)

        # print(ret_dict)
        return ret_dict

    def correct_for(self, col_name, recid_dec_col_name, traits=[]):
        '''
        Across same col_name, correct the attribute for each trait to remove bias
        '''
        if traits == []:
            trait_percentage_dict = self.trait_breakdown(col_name=col_name)
            for trait, percentage in trait_percentage_dict.items():
                traits.append(trait)

        rows_by_trait = self.rows_with(col_name=col_name, traits=traits)
        baseline_error_dict = {}
        baseline_bias_dict = {}
        for trait, group in rows_by_trait.items():
            num_members = len(group)
            total_abs_error = 0
            total_error = 0
            for person in group:
                if int(person[CSVReaderConst.RECIDIVISM_COL_NAME]) == 1:
                    person_error = float(person[recid_dec_col_name]) - CSVReaderConst.HIGHEST_RISK
                else:
                    person_error = float(person[recid_dec_col_name]) - CSVReaderConst.LOWEST_RISK
                total_error += person_error
                total_abs_error += abs(person_error)
            if num_members == 0:
                raise ValueError("No members found in group {0!s}".format(trait))
            baseline_bias = total_error/float(num_members)
            # if mostly over-predicted, baseline bias positive. if under, negative.
            baseline_bias_dict[trait] = baseline_bias
            baseline_error_dict[trait] = total_abs_error
            # print(total_error)
            print("For group {0!s}, baseline error: {1:.3f}, baseline bias: {2:.3f}".format(trait,
                                                                                            total_abs_error,
                                                                                            baseline_bias))

        alt_rows_by_trait = rows_by_trait
        new_error_dict = {}
        new_baseline_dict = {}
        for trait, group in alt_rows_by_trait.items():
            num_members = len(group)
            new_total_error = 0
            total_abs_error = 0
            for person in group:
                # compensate for bias of this group, subtract per person
                corrected_decile = float(person[recid_dec_col_name]) - float(baseline_bias_dict[trait])
                if int(person[CSVReaderConst.RECIDIVISM_COL_NAME]) == 1:
                    person_error = float(corrected_decile) - CSVReaderConst.HIGHEST_RISK
                else:
                    person_error = float(corrected_decile) - CSVReaderConst.LOWEST_RISK
                new_total_error += person_error
                total_abs_error += abs(person_error)
            if num_members == 0:
                raise ValueError("No members found in group {0!s}".format(trait))
            new_baseline_bias = new_total_error/float(num_members)
            new_error_dict[trait] = total_abs_error
            new_baseline_dict[trait] = new_baseline_bias
            print("For group {0!s}, corrected error: {1:.3f}, corrected bias: {2:.3f}".format(trait,
                                                                                              total_abs_error,
                                                                                              new_baseline_bias))

        return baseline_error_dict, baseline_bias_dict, new_error_dict


class AnalyzerShell(cmd.Cmd):
    intro = 'Welcome to the analyzer shell. Type help or ? to list commands.\n'
    prompt = '(analyzer) '
    def setup(self, file_path):
        self.csv_reader = CSVReader(csv_path=file_path)
        self.csv_reader.read_file()

    def do_trait_breakdown(self, arg):
        'Get a percentage and count breakdown of specified argument'
        self.csv_reader.trait_breakdown(col_name=arg.lower(), to_print=True)

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
        self.csv_reader.correct_for(col_name=col_name, recid_dec_col_name=dec_name, traits=traits)

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
