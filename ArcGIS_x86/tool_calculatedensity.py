# -*- coding: utf-8 -*-
"""
Calculate Density Tool

Created on Fri Apr 28 11:21:21 2017

@author: cheny
"""
from arcpy import Parameter
import arcpy
from multiprocessing import cpu_count
import numpy.lib.recfunctions as recfunctions

class CalculateDensityTool(object):
    def __init__(self):
        """Calculate Density Tool"""
        self.label = "1 Calculate Density Tool"
        self.description = "Calculate Density for Fast Search Cluster."
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        #1
        paraminput = Parameter(
                displayName="Input Points",
                name="in_points",
                datatype="DEFeatureClass",
                parameterType="Required",
                direction="Input")
        paraminput.filter.list = ["Point"]
        
        #2
        paramidfield = Parameter(                
                displayName="Identifier Field",
                name="id_field",
                datatype="Field",
                parameterType="Required",
                direction="Input")
        paramidfield.parameterDependencies = [paraminput.name]
        paramidfield.filter.list = ['Short','Long','OID']
        
        #3
        paramweight = Parameter(                
                displayName="Weight Field",
                name="weight_field",
                datatype="Field",
                parameterType="Required",
                direction="Input")
        # Set the filter to accept only fields that are Short or Long type
        paramweight.filter.list = ['Short','Long','Float','Single','Double']
        paramweight.parameterDependencies = [paraminput.name]
        
        #4
        paramoutput = Parameter(
                displayName="Output Result Points",
                name="out_points",
                datatype="DEFeatureClass",
                parameterType="Required",
                direction="Output")
        
        #5
        paramkt = Parameter(
                displayName="Density Kernel Type",
                name="kernel_type",
                datatype="GPString",
                parameterType="Required",
                direction="Input"
                )
        paramkt.filter.list=['CUT_OFF','GAUSS']
        paramkt.value='GAUSS'
        
        #6
        paramcod = Parameter(
                displayName="Cut Off Distance",
                name="cut_off_d",
                datatype="GPDouble",
                parameterType="Required",
                direction="Input"
                )
        paramcod.value="100"
        paramcod.enabled=0
        
        #7
        paramgks = Parameter(
                displayName="Gauss Kernel's Sigma",
                name="gauss_sigma",
                datatype="GPDouble",
                parameterType="Required",
                direction="Input"
                )
        paramgks.value="30"
        
        #8
        paramdevice = Parameter(
                displayName="Device for Calculation",
                name="calc_device",
                datatype="GPString",
                parameterType="Required",
                direction="Input"
                )
        paramdevice.filter.list=['CPU','GPU']
        paramdevice.value='CPU'
        paramdevice.enabled=0
        
        #9
        paramcpuc = Parameter(
                displayName="CPU Parallel Cores",
                name="cpu_cores",
                datatype="GPLong",
                parameterType="Required",
                direction="Input"
                )
        paramcpuc.value=cpu_count()
        
        params = [paraminput,paramidfield,paramweight,
                  paramoutput,paramkt,paramcod,
                  paramgks,paramdevice,paramcpuc]
        return params
    
    def updateParameters(self, parameters):
        params=parameters
        
        if parameters[0].altered and not parameters[1].altered:
            parameters[1].value=arcpy.Describe(parameters[0].valueAsText).OIDFieldName
                
        if params[4].value=='CUT_OFF':
            params[5].enabled=1
            params[6].enabled=0
        else:
            params[5].enabled=0
            params[6].enabled=1
        
        if params[7].value=='CPU':
            params[8].enabled=1
        else:
            params[8].enabled=0     
        return


    def execute(self, parameters, messages):
        
        #get params
        input_feature=parameters[0].valueAsText 
        id_field=parameters[1].valueAsText
        weight_field=parameters[2].valueAsText
        output_feature=parameters[3].valueAsText
        kernel_type=parameters[4].valueAsText
        calc_device=parameters[7].valueAsText
        
        #calculation          
        arrays=arcpy.da.FeatureClassToNumPyArray(input_feature,[id_field,'SHAPE@X','SHAPE@Y',weight_field])
        densities=0
        if calc_device=='CPU':
            from section_cpu import calc_density_cpu
            densities=calc_density_cpu(arrays['SHAPE@X'],arrays['SHAPE@Y'],\
                                   arrays[weight_field],kernel_type,\
                                   parameters[8].value,cutoffd=parameters[5].value,sigma=parameters[6].value)
        
        result_struct=recfunctions.append_fields(recfunctions.drop_fields(arrays,weight_field),\
                                                 'DENSITY',data=densities,usemask=False)
        
        if id_field==arcpy.Describe(input_feature).OIDFieldName:
            sadnl=list(result_struct.dtype.names)
            sadnl[sadnl.index(id_field)]='OID@'
            result_struct.dtype.names=tuple(sadnl)
        
        arcpy.da.NumPyArrayToFeatureClass(result_struct,output_feature,\
                                          ('SHAPE@X','SHAPE@Y'),arcpy.Describe(input_feature).spatialReference)  
        
        return
