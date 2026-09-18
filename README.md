
# VolSlicer

## Highlights

* Create 2D slices of 3D volumes
* Allows for Axial, Coronal, or Sagittal views
* Easy parsing of slices
* Set the voxel spacing

## Overview

This project is a light orthographic slice viewer, where slices are created from either .raw or .vti volumes. The user is expected to provide the volume as well as the (x,y,z) dimensions of it. 

## Usage

* Either run main.py or the included executable.
* To import a volume, click either "Import Volume (raw)" or "Import Volume(vkt)" depending on your volume
* Can also generate an example volume using "Generate Mock Volume" to test
* The "Axis" field allows you to select what view you want
* The "Slice" slider lets you index into specific slices
* The "Voxel Size" boxes allow you to set the (x,y,z) voxel spacing, which should be specific to your volume

## Installation

For now, just clone this repo. In the future I will make a pip package for this.
