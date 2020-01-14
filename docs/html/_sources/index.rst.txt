.. Strohristik Heilung IC2020 documentation master file, created by
   sphinx-quickstart on Tue Jan 14 10:52:37 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Strohristik Heilung IC2020's documentation!
======================================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Models
=====================

Game
====

.. autoclass:: heilung.models.Game
    :members:
    :undoc-members:
    :show-inheritance:
    :inherited-members:

City
=====

.. autoclass:: heilung.models.City
    :members:
    :undoc-members:
    :show-inheritance:
    :inherited-members:

Pathogen
========

.. autoclass:: heilung.models.pathogen.Pathogen
    :members:
    :show-inheritance:
    :inherited-members:
    :undoc-members:

Event
=====

.. autoclass:: heilung.models.event.Event
    :members:
    :show-inheritance:
    :inherited-members:
    :undoc-members:

Action
======

.. autoclass:: heilung.models.action.Action
    :members:
    :show-inheritance:
    :undoc-members:
    :inherited-members:

Heuristics
=====================

StupidHeuristic
===============
.. autoclass:: heilung.heuristics.stupid.StupidHeuristic
    :members:
    :undoc-members:

HumanHeuristic
===============
.. automodule:: heilung.heuristics.human.human
    :members:
    :undoc-members:

.. autoclass:: heilung.heuristics.human.gameplan.Gameplan
    :members:
    :undoc-members:

.. autoclass:: heilung.heuristics.human.stateheuristic.Stateheuristic
    :members:
    :undoc-members:

EnsembleHeuristic
=================
.. automodule:: heilung.heuristics.ensemble.ensemble
    :members:
    :undoc-members:
