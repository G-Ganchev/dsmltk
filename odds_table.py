# -*- coding: utf-8 -*-
"""
Created on Thu Jun 25 17:35:27 2020

@author: GeorgiGanchev
"""


import pandas as pd 
import numpy as np 
from pandas.api.types import is_string_dtype
from pandas.api.types import is_numeric_dtype 
from pandas.api.types import is_categorical_dtype
from pandas.api.types import is_datetime64_any_dtype
from pandas.api.types import is_bool_dtype


class odds_table():
    """ 
    Creates a pandas.DataFrame containing Odds Index and basic stats.
    
    Args:
        name (str):
        p_cls_label (str):
        n_cls_label (str):
        cuts (int):
            
        X (pandas.Series): variable to be analyzed
        y (pandas.Series): binary outcome variables [0,1]
            
    Returns:
        pandas.DataFrame
    """
    def __init__(self,name:str ='Odds Table',
                     p_cls_label :str ='postive',
                     n_cls_label:str='negative',
                     cuts :int = 10):
        self.table = None
        self.name = name
        self.p_cls_label = p_cls_label
        self.n_cls_label = n_cls_label
        self.cuts = cuts
        
    def __version__(self):
        return '0.1.0'
        
    def compute_table(self,X,y,return_result = False):
        if is_numeric_dtype(X) or is_datetime64_any_dtype(X):
            X = pd.qcut(X,self.cuts,duplicates='drop')
        elif is_string_dtype(X):
            X = X.astype('category')
        X = X.cat.add_categories(['MISSING'])
        X = X.fillna("MISSING")
        self.X_name = X.name
        
        df = pd.DataFrame({X.name :X.values,
                           y.name: y.values})
        
        self.total_odds = df[y.name].sum()/(len(df[y.name]) - df[y.name].sum())
        
        df = df.groupby(X.name).agg({y.name:[np.sum,'count']}).reset_index()
        df.columns = [X.name,'positive','total']
        df['negative'] = df['total'].values - df['positive'].values 
        df['group_odds'] = df['positive'].values/df['negative'].values
        df['total_odds'] = self.total_odds
        df['odds_index'] = df.apply(self._cmpt_odds,axis=1)
        df = df[[X.name,'positive','negative','total','group_odds','total_odds','odds_index']]
        df['% positive'] = df['positive']/df['total'].sum()
        df['% negative'] = df['negative']/df['total'].sum()
        df['% total'] = df['total']/df['total'].sum()
        df['WOE'] = np.log(df['% positive']/df['% negative'])
        
        df.rename(columns={'positive':self.p_cls_label,
                                'negative':self.n_cls_label,
                                '% positive':'% {}'.format(self.p_cls_label),
                                '% negative':'% {}'.format(self.n_cls_label)},
                    inplace=True)
        self.table = df
        if return_result:
            return self.table
    
    def _cmpt_odds(self,row):
        if row['group_odds'] ==0:
            return float('-inf')
        elif row['group_odds'] >= row['total_odds']:
            return np.round(row['group_odds']/row['total_odds'] *100 -100)
        else:
            return np.round(row['total_odds']/row['group_odds'] *-100 +100)
        
    def to_excel(self,file):
        writer = pd.ExcelWriter(file, engine='xlsxwriter')
        sheet_name = self.X_name
        self.table.to_excel(writer, sheet_name=sheet_name,index=False)

        workbook = writer.book
        worksheet = writer.sheets[sheet_name]
        # Create a chart object.
        chart = workbook.add_chart({'type': 'column'})

        # Configure the series of the chart from the dataframe data.
        chart.add_series({
        'values':     '=' + sheet_name + '!$G$2:$G$'+str(self.table.shape[0] + 1),
        'categories': '=' + sheet_name + '!$A$2:$A$'+str(self.table.shape[0] + 1),
        'gap':        2,
        })

        worksheet.insert_chart('O2', chart)
        writer.save()
        
    
##Test Code
##seed for reproducibility
#np.random.seed(200)
#
#df = pd.DataFrame({"a": np.random.rand(3000),
#                    "b":[0,1,0]*1000,
#                    "c":np.random.rand(3000)})    
#ot = odds_table()
#ot.compute_table(df['a'],df['b'])
#ot.to_excel('ot.xlsx')        