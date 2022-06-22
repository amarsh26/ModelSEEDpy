# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging
import re
from optlang.symbolics import Zero, add
import json as _json
from cobra.core import Gene, Metabolite, Model, Reaction
from modelseedpy.fbapkg.mspackagemanager import MSPackageManager
from modelseedpy.core.msmodelutl import MSModelUtil
from modelseedpy.core.exceptions import FeasibilityError  # moved excpetion classes to a designated exceptions file for broader use

class BaseFBAPkg:
    """
    Base class for FBA packages
    """
    def __init__(self, model, name, variable_types={}, constraint_types={},reaction_types = {}):
        self.model = model
        self.modelutl = MSModelUtil(model)
        self.name = name
        self.pkgmgr = MSPackageManager.get_pkg_mgr(model)
        if self.pkgmgr is None:
            self.pkgmgr = MSPackageManager.get_pkg_mgr(model,1)
        self.pkgmgr.addpkgobj(self)
        self.constraints = dict()
        self.variables = dict()
        self.parameters = dict()
        self.new_reactions = dict()
        self.variable_types = variable_types
        self.constraint_types = constraint_types
        
        for type in variable_types:
            self.variables[type] = dict()
        for type in constraint_types:
            self.constraints[type] = dict()
    
    def validate_parameters(self, params, required, defaults):
        for item in required:
            if item not in params:
                raise ValueError(f'Required argument {item} is missing!')
        self.parameters.update(defaults)  # we assign all defaults
        self.parameters.update(params)  # replace defaults with params
    
    def clear(self):
        objects = []
        for type in self.variables:
            for object in self.variables[type]:
                objects.append(self.variables[type][object])
        for type in self.constraints:
            for object in self.constraints[type]:
                objects.append(self.constraints[type][object])
        self.model.remove_cons_vars(objects)
        self.variables = {}
        self.constraints = {}
        
    def build_variable(self,type,lower_bound,upper_bound,vartype,object = None):
        name = None
        if self.variable_types[type] == "none":
            count = len(self.variables[type])
            name = str(count+1)
        elif self.variable_types[type] == "string":
            name = object
        else:
            name = object.id
        if name not in self.variables[type]:
            self.variables[type][name] = self.model.problem.Variable(name+"_"+type, lb=lower_bound,ub=upper_bound,type=vartype)
            self.model.add_cons_vars(self.variables[type][name])
        return self.variables[type][name]
        
    def build_constraint(self,type,lower_bound,upper_bound,coef = {},object = None):
        name = None
        if self.constraint_types[type] == "none":
            count = len(self.constraints[type])
            name = str(count+1)
        elif self.constraint_types[type] == "string":
            name = object
        else:
            name = object.id
        if name in self.constraints[type]:
            self.model.remove_cons_vars(self.constraints[type][name])
        self.constraints[type][name] = self.model.problem.Constraint(
            Zero,lb=lower_bound,ub=upper_bound,name=name+"_"+type
        )
        self.model.add_cons_vars(self.constraints[type][name])
        self.model.solver.update()
        if len(coef) > 0:
            self.constraints[type][name].set_linear_coefficients(coef)
        self.model.solver.update()
        return self.constraints[type][name]
    
    def all_variables(self):
        return self.pkgmgr.all_variables()
    
    def all_constraints(self):
        return self.pkgmgr.all_constraints()
    
    def add_variable_type(self,name,type):
        if name not in self.variables:
            self.variables[name] = dict()
        if name not in self.variable_types:
            self.variable_types[name] = type
            
    def add_constraint_type(self,name,type):
        if name not in self.constraints:
            self.constraints[name] = dict()
        if name not in self.constraint_types:
            self.constraint_types[name] = type
