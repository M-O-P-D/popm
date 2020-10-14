#!/usr/bin/env python

import os
import argparse
import glob
import pandas as pd

def run(config):

  tables = {"[0-9]": "", "_locations": "_locations", "_allocations": "_allocations"}

  for t in tables.keys():
    pattern = "scenario/%s%s*.csv" % (config, t)
    files = glob.glob(pattern)
    df = pd.DataFrame()
    for f in files:
      df = df.append(pd.read_csv(f), ignore_index=True)
      os.remove(f)
    df.to_csv("scenario/%s%s.zip" % (config, tables[t]), compression="zip", index=False)


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="popm batch output concat script")
  parser.add_argument("config", type=str, help="the model configuration (without .json)")
  args = parser.parse_args()

  run(args.config)
