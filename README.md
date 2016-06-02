# Running Caffe on titan

A little messy repo as it started as kind of my diary.

* `plots` contains a few scripts to extract some info from Caffe log files;
they are not really general with some hard-coded variables, but they may be
used as a starting point so I decided to keep them

* `xview` contains configuration files for first attempt to run x view only

* `xuv` contains configutration files for 3-view epsilon net

## Caffe workflow

There is a README in `caffe_workflow` which describes `mlmpr_caffe`.
Here is just a general summary and an example how to use it.

### Depend or not depend

First version of the script (`mlmpr_caffe.py`) requires jobs to finish
within 2-hours walltime. The genral idea is to have `max_iter` which defines
number of iteration per job and `last_iter` which defines total number of
iterations. Whenever job is done (when `max_iter` is reached) it submits itself
with modified solver (so new `max_iter = current_run * max_iter`).
The recursion lasts until `last_iter` is reached.

The new and recommended version (`mlmpr_caffe_depend.py`) uses `depend` flag
for `qsub` to run jobs recursively, as explained below.

### Workflow step by step

The script runs with two modes: `new` (start new job) or `advance`
(continue existing job).

To run a new job one needs a configuration file, like `caffe_workflow/epsilon_126x50_xuv.ini`:

```
[path]
myself    = /lustre/atlas/proj-shared/hep105/caffe_titan/caffe_workflow/mlmpr_caffe_depend.py
caffe     = /lustre/atlas/proj-shared/hep105/steven_caffe2/caffe
snapshots = /lustre/atlas/proj-shared/hep105/caffe_titan/caffe_workflow/xuv/snapshots
logs      = /lustre/atlas/proj-shared/hep105/caffe_titan/caffe_workflow/xuv/logs
solver    = /lustre/atlas/proj-shared/hep105/caffe_titan/xuv/epsilon_127x50_xuv_solver.prototxt

[caffe]
; optional solver modifications
max_iter = 150000
test_iter = 1500
snapshot = 5000
display = 5000
test_interval = 5000
```

* `path` section is required
    * `myself` is a path to the script
    * `caffe` is a path to the Caffe's top dir
    * `snapshots` is a path to folder to save snapshots
    * `logs` is a path to folder to save logs
    * `solver` is a path to Caffe's solver

* everything in `caffe` section is optional; the script loops over everything
there and update solver if some line starts with something defines in `caffe`

* solver contains the path to network configuration

* network configuration contains the path to HDF5 file lists

* HDF5 file lists contain paths to HDF5 files

* see example in `xview` or `xuv`

To start a job simply call:

```
./mlmpr_caffe_depend.py new --config [path to my config file]
```

Optionally, `--name` flag can be used to define the job name
(default = mlmpr_caffe). Either way, a timestamp will be added to make sure that
the name is unique and no logs will be overwritten.

The following file are created in `logs` directory:

* `[job_name].pbs` - PBS script to be run

* `[job_name]_updater.pbs` - PBS script to be called when job is killed

* `[job_name].prototxt` - copy of network configuration file

* `[job_name].solver` - copy of `solver` with updated path to net conf
and all modifications defined in `[caffe]`

* `[job_name].ini` - copy of configuration file with new section `[status]`,
which contains:

    * `name` - job name
    * `current_run`
    * `prototxt` - path to `[job_name].prototxt`
    * `solver` - path to `[job_name].solver`
    * `updater` - path to `[job_name]_updater.pbs`

* `[job_name]_[run_number].out` - Caffe logs

The initial job is run with:

```
qsub -W depend=afternotok:$PBS_JOBID [job_name]_updater.pbs
```

which means that "updater" is called if job exit with status different than 0.

Updater just call:

```
./mlmpr_caffe_depend.py advance --status [job_name].ini
```

When script is run in `advance` mode:

* `current_run` is updated in status file
* the last snapshot from `snapshots` folder is taken
* another Caffe job is called but with `--snapshot` flag
* new updater is created etc
* until `max_iter` is reached

Comments:

* if you want to run more epochs, just update status `[job_name].solver`
and use `./mlmpr_caffe_depend.py advance ...`

* be careful with Caffe's `snapshot` parameter
(which defines how many iterations a snapshot is created);
you do not want to snapshotting to often;
but it is good to have a few snapshots per job;
e.g. imagine 9000 iterations are done within 2 hours and you do snapshots
every 5000 iterations...
you lose 4000 iterations as next job will start from the last snapshot

* note that `./mlmpr_caffe_depend.pt new` have some optional flags to change
learning rate, batch size etc from command line; check them all with
`./mlmpr_caffe_depend.py new --help`
