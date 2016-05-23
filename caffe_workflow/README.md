# MLMPR Caffe @ Titan

Note: `mlmpr_caffe_depend.py` uses:

```
qsub -W depend=afternotok:$PBS_JOBID next_job
```

so there is no need to make sure the job is done within 2 hours.
It will run a job and "updater" will be in hold until the job is killed.
If the job ends with error "updater" will run next job starting with last
checkpoint (until max_iter is reached).

---


```
Usage: mlmpr_caffe.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  advance  Continue job saved with last checkpoint saved...
  new      Prepare a job based on config file.
```

The script organizes running Caffe jobs within 2 hours wall time limit.
There are two modes: one to initialize the job and the other to restart job
using last checkpoint.

The initialization is based on configuration file, example:

```
[path]
myself    = /lustre/atlas/proj-shared/hep105/caffe_titan/caffe_workflow/mlmpr_caffe.py
caffe     = /lustre/atlas/proj-shared/hep105/steven_caffe2/caffe
snapshots = /lustre/atlas/proj-shared/hep105/caffe_titan/caffe_workflow/snapshots
logs      = /lustre/atlas/proj-shared/hep105/caffe_titan/caffe_workflow/logs
solver    = /lustre/atlas/proj-shared/hep105/caffe_titan/minosmatch_nukecczdefs_127x50_x_unshifted_me1Bmc_solver.prototxt

[caffe]
; max_iter is per job and it is required
; last_iter defines when to stop recursion
; if last_iter is not defined, the job will submit itself until killed by hand
last_iter = 15000
max_iter = 1000
display = 500
```

The `path` section includes all necessary paths to run the job:

* `myself` - path to `mlmpr_caffe.py` script
* `caffe` - top Caffe's directory
* `snapshots` - place to save Caffe snapshots
* `logs` - place for: `pbs` script, `pbs` output, solver and config clones

To start the job sequence use:

```
./mlmpr_caffe.py new --config config_file [--name job_name]
```

* wheter `--name` is provided or not the timestamp is attached to avoid
job name duplicates; this name is used as a base for all logs files,
snapshots prefix etc;

* `paths` are created if necessary

* `config` file is clone to `logs`; `name` is saved in `status` section for future reference; `current_run` (used to generate next `max_iter`) is also saved in `status`

* `solver` is also clone to `logs`; everything defined in `caffe` section overwrites corresponding parameters from original solver; `max_iter` is required and it defines the number of iterations per job; `last_iter` defines the end of self-submitting

* `pbs` script is generated the way it calls `mlmpr_caffe.py advance` recursively (until job is killed or `last_iter` is reached)

The continuation of already initialized job:

```
./mlmpr_caffe.py advance --status config_clone
```

* update `current_run` in config/status file

* update `solver`, so max_iter = max_iter * current_run

* look for last snapshot and update `pbs` script accordingly

* run itself until `last_iter` is reached
