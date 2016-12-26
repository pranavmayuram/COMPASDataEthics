<p align="center"><img src="https://www.eecs.umich.edu/eecs/images/EECS-Logo-Mobile.png" width="200"></p>
# COMPASDataEthics

####Introduction

This project is based on an article written by ProPublica about demographic bias in the COMPAS criminal risk assessment system.
Their finding can be seen via their article, and Github repo.

The analysis can be done on any similarly formatted CSV file using the Python scripts written for our analysis.
The Python scripts create a command line interface to make generating the plots, and analysis with ease.

####Types of Error & Bias Analysis

*Below, "demographic" refers to a trait within a column, i.e. "Asian" within the "race" column is an example of a demographic*

There are 3 types of analysis we conducted:
* Linear bias correction
    * Detected correctness/incorrectness using predicted recidivism score vs. actual recidivism (translated to a score).
* Threshold bias/error detection
    * Plots all potential values for a threshold which would divide where recidivism is predicted/not predicted
    * This can be printed for every demographic to see which threshold provides the lowest error
* Non-uniform bias correction
    * Corrects based on the predicted decile score for each demographic
    * For example, it would do the same correction as the linear bias correction, but instead of correcting per demographic, it would 
    correct per predicted decile score within a demographic
        * i.e. linear bias correction would do bias correction for the demographic "Asian" within the "race" column, whereas non-uniform bias correction 
        would correct for "Asian" within "race" with a predicted decile score (risk score) of 7, essentially treating all Asians with a predicted score of 7 as their own demographic to perform bias correction on.