#!/usr/bin/env python

import argparse
import tarfile

# TODO put this in utils so it runs as part of the job?
def run(config):

  files = [".json", ".csv", "_locations.csv", "_allocations.csv", "_resources.csv", "_resources_baseline.csv" ]

  with tarfile.open("scenario/%s.tgz" % config, "w:gz") as tar:
    for f in files:
      file = "%s%s" % (config, f)
      tar.add("scenario/%s" % file, arcname=file)

if __name__ == "__main__":

  parser = argparse.ArgumentParser(description="popm batch output tar script")
  parser.add_argument("config", type=str, help="the model configuration (without .json)")
  args = parser.parse_args()

  run(args.config)
