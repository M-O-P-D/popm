#!/usr/bin/env python

from pathlib import Path
import argparse
import glob
import pandas as pd
import shutil
import tarfile

def run(config):

  tables = {"[0-9]": "", "_locations": "_locations", "_allocations": "_allocations", "_resources": "_resources" }

  Path("scenario/%s" % config).mkdir(exist_ok=True)
  shutil.copyfile("scenario/%s.json" % config, "scenario/%s/%s.json" % (config, config))

  for t in tables.keys():
    pattern = "scenario/%s%s*.csv" % (config, t)
    files = glob.glob(pattern)
    if not files:
      raise ValueError("no files found matching '%s'" % pattern)
    df = pd.DataFrame()
    for f in files:
      df = df.append(pd.read_csv(f), ignore_index=True)
      Path(f).unlink() # delete file
    print(df.head(), len(df))
    # saving as compressed file is broken
    df.to_csv("scenario/%s/%s%s.csv" % (config, config, tables[t]), index=False)

    with tarfile.open("scenario/%s.tgz" % config, "w:gz") as tar:
      tar.add("scenario/%s" % config) #, arcname=os.path.basename(source_dir))


if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="popm batch output concat script")
  parser.add_argument("config", type=str, help="the model configuration (without .json)")
  args = parser.parse_args()

  print("DEPRECATED, use concat.sh")
  run(args.config)
