
import numpy as np
import pandas as pd
from pandas import ExcelWriter
from pathlib import Path

import seaborn as sns
import matplotlib.pyplot as plt

scenarios = ["7-small", "13-small", "19-small", "3-medium", "6-medium", "8-medium", "1-large", "2-large", "3-large"]

def label_points(x, y, val, ax):
    a = pd.concat({'x': x, 'y': y, 'val': val}, axis=1)
    for i, point in a.iterrows():
        ax.text(point['x']+.02, point['y'], str(point['val']))


if __name__ == "__main__":

  data_path = Path("./model-output")

  # collate into spreadsheet
  # with ExcelWriter(data_path / "collated.xlsx") as fd:
  #   for scenario in scenarios:
  #     mean = pd.read_csv(data_path / scenario / "mean_dep_times.csv", index_col="Event")
  #     stddev = pd.read_csv(data_path / scenario / "stddev_dep_times.csv", index_col="Event")
  #     mean.to_excel(fd, sheet_name=scenario)
  #     stddev.to_excel(fd, sheet_name=scenario+"-stddev")

  with ExcelWriter(data_path / "outliers.xlsx") as fd:
    for scenario in scenarios:
      data = pd.read_csv(data_path / scenario / "mean_dep_times.csv", index_col="Event")

      df = pd.DataFrame(index=[1,2,3,4,38,39,40,41])
      for col in data.columns.values:
        top = data.sort_values(by=col).head(4).index.values
        bot = data.sort_values(by=col).tail(4).index.values

        #print(np.concatenate(top, bot))
        df[col] = top.tolist() + bot.tolist()      

      print(df)
      df.to_excel(fd, sheet_name=scenario)

    # print(data.head())
    # data = data / data.mean()
    # #data[data])
    # sns.scatterplot(data=data.T, legend=False)
    # break



  plt.show()
    
