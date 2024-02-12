# ChemSCAD

## Screenshots:

Main interface:

![](images/screen.png "")

Choice dialog box:

![](images/screen3.png "")

Reactor dialog box:

![](images/screen2.png "")

Canula dialog box:

![](images/screen4.png "")


## OpenSCAD installation:

ChemSCAD requires Python **3.6** or above. Tested and working with latest Python release (3.8).

ChemSCAD was tested with OpenSCAD 2019-05 (most up-to-date version as of March 2020)

- Install OpenSCAD for your operating system as follows:


For Windows:

All OpenSCAD dependencies including the binaries are included in the setup.py for ChemSCAD, so will be installed automatically when installing the requirements.txt file.

Therefore, please proceed to the ChemSCAD installations instructions below.


For Mac:

OpenSCAD can be installed using the .dmg installable from the following link: https://files.openscad.org/OpenSCAD-2019.05.dmg

Install this .dmg file, making sure to accept all permissions in Security & Privacy from within System Preferences.


For Ubuntu: 

```
sudo add-apt-repository ppa:openscad/releases
sudo apt-get update
sudo apt-get install openscad
sudo apt-get install python-dev graphviz libgraphviz-dev pkg-config mesa-common-dev libglu1-mesa-dev -y
```

## ChemSCAD installation:

Prior to installing ChemSCAD it is recommended to make a virtual environment (venv) in order to not have any conflicts with existing installed pip packages.

PyQt5 _may_ have to be installed manually, dependent on your installation. Install with:

```
pip install PyQt5
```

Installation is simple, simply pip-install the `chemscad` package:

```
pip install chemscad
```

ChemSCAD can now be run from a command line using the command: `chemscad`

## ChemSCAD updates:

When bug fixes and new features are released for ChemSCAD, you may wish to update to the latest version. Simply install via Pip again for the latest version:

```
pip install chemscad
```

**For developers ONLY**

If you wish to work on fixing a bug or implementing a new feature in ChemSCAD you may do so by creating a **Feature** branch from the **dev** branch as follows:

N.B: the following instructions assume you are currently on the **master** branch and have performed git add and git commit to clean the working tree prior to moving branches.

```
git checkout -b dev # moves current branch from master to dev
git checkout -b [new-branch] # switches from new branch from dev & creates new branch from dev for new feature/bug fix
git push -u origin [new-branch] # sets new branch to track local changes on the remote origin host
```
Once a new feature/bug fix is added and tested as working, create a **merge request** to merge **new-branch** into **dev** and eventually merge **dev** into **master** to release the new stable build of ChemSCAD with new features and bug fixes implemented.








# Development

ChemSCAD uses the [Black](https://github.com/ambv/black) code formatter. A
pre-commit hook is included in the repo. Install the dependencies of this
repo (requirements.txt), and before you submit any commit, just run:

```
pre-commit install
```

Any commit you run after that will first trigger Black and will format your
code properly. Run the following command at any point if you're not sure
your code is not formatted properly (recursive command).

```
black .
```
