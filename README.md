# Python Ball Motion Tracking (**pybmt**)

Python Ball Motion Tracking (`pymbt`) is a python interface for running Richard J. Moore's [FicTrac](https://github.com/rjdmoore/fictrac) in a closed loop manner. The goal of **pybmt** is to allow researchers to easilly run **FicTrac** from a python program and allow tracking information to be processed in realtime for closed loop experiments. Since **pybmt** is not a replacement for fictrac, the user is expected to be experienced with configuring and calibrating it. This code handles all the details of spawning, managing, and communicating state of fictrac using a simple python based API. We hope that it will be a useful tool for researcher wishing to build their closed loop experiments in python.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. 

### Prerequisites

**pybmt** requires a working version of **FicTrac** to be present on the system. Currently, the only supported version of **FicTrac** is a [our forked version](https://github.com/murthylab/fictrac/tree/control_features) of **FicTrac Version 2.0**. Check the [releases page]() for pre-built binaries for your system. We hope to have these changes merged into the upstream [FicTrac GitHub repo](https://github.com/rjdmoore/fictrac) in the near future. 

```
Give examples
```

### Installing

A step by step series of examples that tell you how to get a development env running

Say what the step will be

```
Give the example
```

And repeat

```
until finished
```

End with an example of getting some data out of the system or using it for a little demo

## Running the tests

Explain how to run the automated tests for this system

### Break down into end to end tests

Explain what these tests test and why

```
Give an example
```

### And coding style tests

Explain what these tests test and why

```
Give an example
```

## Built With

* [FicTrac](https://github.com/rjdmoore/fictrac) - **FicTrac** provides all the tracking!
* [ZeroMQ](http://www.zeromq.org/) - Low-latency cross platform messaging  

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/murthylab/pybmt/tags). 

## Authors

* **David Turner** - __Princeton University__ 

See also the list of [contributors](https://github.com/murthylab/pybmt/contributors) who participated in this project.

## License

This project is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License - see the [LICENSE.md](LICENSE.md) file for details.

## Research

If you use **pybmt** and **FicTrac** as part of your research, please cite the original FicTrac publication:

> RJD Moore, GJ Taylor, AC Paulk, T Pearson, B van Swinderen, MV Srinivasan (2014). *"FicTrac: a visual method for tracking spherical motion and generating fictive animal paths"*, Journal of Neuroscience Methods, Volume 225, 30th March 2014, Pages 106-119. [[J. Neuroscience Methods link]](https://doi.org/10.1016/j.jneumeth.2014.01.010) [[Preprint (pdf) link]](https://www.dropbox.com/s/sw6qcmphk417bgi/2014-Moore_etal-JNM_preprint-FicTrac.pdf?dl=0)

## Acknowledgments

* **Richard Moore** - author of **FicTrac**
