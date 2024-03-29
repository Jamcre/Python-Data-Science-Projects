"""
Name:  James Michael Crespo
Email: james.crespo64@myhunter.cuny.edu
Resources: the internet
"""
import pandas as pd
import numpy as np


def import_data(file_name):
    """
    Function has 1 input, reads in file, returns a df with 51 rows: the 1st row for United States,
    also a row for each state, and District of Columbia. Cols of df should be arranged as:
    All null values should be filled with 0.
    The 1st column named Locale, contains name of area. The first row should be United States,
    followed by states in alphabetical order: Alabama,..., Wymoning (order in initial datasets).
    NOTE: Excluding Puerto Rico and US Territories b/c they're not counted in overall estimates.
    The 2nd column named Total, contains the total population for each row.
    The 3rd column named Stayed, contains sum of those who stayed in same house and stat
    (i.e. the sum of two columns from the initial excel file).
    The subsequent columns contain number of new residents to the state, by previous location.
    Example, the third column, Alabama contains number of new residents to Alabama from each state.
    For row Alabama, this cell (e.g. df.loc['Alabama','Alabama']) is 0, because it's same state.
    For row Alaska, this cell (e.g. df.loc['Alabama','Alaska']), is the number of people
    who moved from Alaska to Alabama this past year.
    In the case of 2019 data, there were 1,105 people who lived in Alaska and moved to Alabama.
    The row, United States2, has the total number of people for its first column,
    the number of people who didn't move, followed by the total who moved into each state.
    Drop all other columns, such as totals, territorial information, repetitions of the row labels
    The returned DataFrame should have 52 rows and 54 columns.

    :param file_name: name of a .xls file from State-to-State Migration Flows from the US Census.
    """
    # Read in file
    df = pd.read_excel(file_name, skiprows=7, skipfooter=11)
    # Drop empty rows
    df = df.dropna(subset=['Unnamed: 0'])
    # Drop duplicate column heading in the middle row of xls file
    df = df.drop(36)
    # Reset indices
    df = df.reset_index(drop=True)
    # Drop duplicate column headings
    duplicate_headings = [f'Unnamed: {i}' for i in range(11, 132, 11)]
    df = df.drop(duplicate_headings,axis=1)
    # Convert NaN to 0, and change all columns to int64 type, except 1st column
    df = df.fillna(0)
    df.iloc[:, 1:] = df.iloc[:, 1:].astype('int64')
    # Rename 'Locale' column
    df.rename(columns={'Unnamed: 0' : 'Locale'}, inplace=True)
    # Rename 'Total' column
    df.rename(columns={'Estimate': 'Total'}, inplace=True)
    # Calculate 'Stayed' column, drop columns after finished
    stayed_lst = df['Estimate.1'] + df['Estimate.2']
    df.insert(2, 'Stayed', stayed_lst)
    df = df.drop(['Estimate.1', 'Estimate.2'], axis=1)
    # Drop all MOE columns
    df = df.drop('MOE',axis=1)
    moe_headings = [f'MOE.{i}' for i in range(1, 59, 1)]
    df = df.drop(moe_headings,axis=1)
    # Drop values for Abroad Migration
    abroad_vals_headings= [f'Estimate.{i}' for i in range(55, 59, 1)]
    df = df.drop(abroad_vals_headings,axis=1)
    # Drop dif in state of residence column
    df = df.drop('Estimate.3',axis=1)
    # Rename columns to reflect states
    state_names = df['Locale'].iloc[1:]
    estimate_headings = [f'Estimate.{i}' for i in range(4, 55, 1)]
    df = df.rename(columns=dict(zip(estimate_headings,state_names)))
    # Return clean df
    return df


def make_transition_mx(df):
    """
    Function has 1 input. Returns a transition matrix, vals range from 0 - 1, each column sums to 1
    The entries represent the fraction of the population that migrated to that state,
    with the diagonals being the population that stayed (didn't move).

    :param df: a df with columns, Locale, Total, Stayed, followed by states' data.
               The first row (for locale United States2) is ignored and,
               the subsequent rows should contain the states in the same order as the column labels
    """
    # Drop the first row
    df = df.drop(index=0)
    # Extract the relevant data
    pop_data = df.iloc[:, 3:].values
    total_pop = df['Total'].values
    # Create the transition matrix
    transition_mx = pop_data / total_pop[:, np.newaxis]
    # Fill the diagonal with the fraction of the population that stayed
    np.fill_diagonal(transition_mx, df['Stayed'] / total_pop)
    return transition_mx

def moving(transition_mx, starting_pop, num_years = 1):
    """
    Function has 3 inputs and returns an array with the population of each state after num_years.

    :param transition_mx: a square array of values between 0 and 1. Each column sums to 1.
    :param starting_pop: a 1D array of positive numeric values, same length as transition_mx.
    :param num_years: name of col with dependent variable (predicted) in the model. default = 1.
    """
    # Get pop after 'num_years' using the transition matrix
    current_pop = starting_pop
    for _ in range(num_years):
        current_pop = np.dot(transition_mx, current_pop)
    return current_pop

def steady_state(transition_mx, starting_pop):
    """
    This function has 2 inputs. Returns array of the population of each state at the steady state.
    That is, it returns the eigenvector corresponding to the largest eigenvalue,
    scaled so that it's entries sum to 1, then multiplied by the sum of the starting populations.

    :param transition_mx: a square array of values between 0 and 1. Each row sums to 1.
    :param starting_pop: a 1D array of positive numeric values, same length as transition_mx.
    """
    eig_val, eig_vec = np.linalg.eig(transition_mx)
    steady_state_pop = eig_vec[:, np.argmax(eig_val)]
    steady_state_pop /= steady_state_pop.sum()
    return steady_state_pop * starting_pop.sum()


def main():
    """
    Function tests
    """
    df_2019 = import_data('program9/State_to_State_Migrations_Table_2019.xls')
    print(df_2019)

    tr_mx = make_transition_mx(df_2019)
    print(tr_mx)

    df_ca_ny = df_2019[ ['Locale','Total','Stayed','California','New York'] ]
    df_ca_ny = df_ca_ny[ df_ca_ny['Locale'].isin(['United States2','California','New York']) ]
    print(df_ca_ny)
    tr_mx_ca_ny = make_transition_mx(df_ca_ny)
    np.set_printoptions(precision=3, suppress=True)
    print(tr_mx_ca_ny)
    other = np.ones(2) - (tr_mx_ca_ny[0]+tr_mx_ca_ny[1])
    tr_mx_ca_ny = np.concatenate((tr_mx_ca_ny,[other]),axis=0)
    other_2_ny = (df_ca_ny.iloc[2,1]-(df_ca_ny.iloc[2,2]+df_ca_ny.iloc[2,3]))/df_ca_ny.iloc[2,1]
    other_2_ca = (df_ca_ny.iloc[1,1]-(df_ca_ny.iloc[1,2]+df_ca_ny.iloc[1,3]))/df_ca_ny.iloc[2,1]
    other_2_other = 1.0 - (other_2_ca + other_2_ny)
    others = np.array([[other_2_ca], [other_2_ny], [other_2_other]])
    tr_mx_ca_ny = np.append(tr_mx_ca_ny,others,axis=1)
    print(tr_mx_ca_ny)

if __name__ == "__main__":
    main()
