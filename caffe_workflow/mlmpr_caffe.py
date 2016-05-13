#!/usr/bin/env python
"""
Recursive workaround for 2 hours walltime.
"""
import click
from ConfigParser import SafeConfigParser
import os
from datetime import datetime as date
import subprocess


def check_paths(paths):
    """Create missing paths."""
    for p in paths:
        if not os.path.exists(p[1]):
            os.makedirs(p[1])


def make_unique(name):
    """Just to make sure there are no name duplicates."""
    return name + "_" + date.now().isoformat()


def generate_pbs(cfg, init=False):
    """Generate PBS script."""
    pbs = cfg.get("path", "logs") + "/" + cfg.("status", "name") + ".pbs"
    out = cfg.get("path", "logs") + "/" + cfg.("status", "name") + ".out"
    err = cfg.get("path", "logs") + "/" + cfg.("status", "name") + ".err"

    pbsf = open(pbs, 'w')

    print pbsf, "#!/bin/bash"
    print pbsf, "#PBS -A hep105"
    print pbsf, "#PBS -l nodes=1"
    print pbsf, "#PBS -l walltime=2:00:00"
    print pbsf, "#PBS -N", cfg.("status", "name")
    print pbsf, "#PBS -o", out
    print pbsf, "#PBS -e", err

    print pbsf, "source $MODULESHOME/init/bash"
    print pbsf, "source $PROJWORK/hep105/steven_caffe2/bashsetup.execenv.sh"
    print pbsf, "module load cray-mpich"

    print pbsf, "aprun -n 1 -N 1", \
                cfg.get("path", "caffe") + "/build/tools/caffe train", \
                "--solver=" + cfg.("caffe", "solver")

    pbsf.close()

    return pbs


def submit(pbs):
    """qsub the script"""
    cmd = "qsub -q titan", pbs
    subprocess.Popen(cmd, shell=True, executable="/bin/bash")


@click.group()
def main():
    pass


@main.command()
@click.option('--config', help='config ini file', required=True)
@click.option('--name', help='job name', default=None)
def new(config, name):
    """Prepare a job based on config file."""
    cfg = SafeConfigParser()
    cfg.read(config)

    check_paths(cfg.items('path'))

    jobname = make_unique(name or "mlmpr_caffe")

    cfg.add_section("status")
    cfg.set("status", "name", jobname)

    statusfile = cfg.get("path", "logs") + "/" + jobname + ".ini"
    with open(statusfile, 'wb') as configcopy:
        cfg.write(configcopy)

    pbs = generate_pbs(cfg, True)

    submit(pbs)

if __name__ == '__main__':
    main()
