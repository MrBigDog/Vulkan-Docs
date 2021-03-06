#!/usr/bin/python3 -i
#
# Copyright (c) 2013-2018 The Khronos Group Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os,re,sys
from generator import *

# ExtensionMetaDocGeneratorOptions - subclass of GeneratorOptions.
class ExtensionMetaDocGeneratorOptions(GeneratorOptions):
    """Represents options during extension metainformation generation for Asciidoc"""
    def __init__(self,
                 filename = None,
                 directory = '.',
                 apiname = None,
                 profile = None,
                 versions = '.*',
                 emitversions = '.*',
                 defaultExtensions = None,
                 addExtensions = None,
                 removeExtensions = None,
                 sortProcedure = regSortFeatures):
        GeneratorOptions.__init__(self, filename, directory, apiname, profile,
                                  versions, emitversions, defaultExtensions,
                                  addExtensions, removeExtensions, sortProcedure)

# ExtensionMetaDocOutputGenerator - subclass of OutputGenerator.
# Generates AsciiDoc includes with metainformation for the Vulkan extension
# appendices. The fields used from <extension> tags in vk.xml are:
#
# name     extension name string
# number   extension number (optional)
# type     'instance' | 'device' (optional)
# requires list of comma-separate requires Vulkan extensions (optional)
# contact  name and github login or email address (optional)
#
# ---- methods ----
# ExtensionMetaDocOutputGenerator(errFile, warnFile, diagFile) - args as for
#   OutputGenerator. Defines additional internal state.
# ---- methods overriding base class ----
# beginFile(genOpts)
# endFile()
# beginFeature(interface, emit)
# endFeature()
class ExtensionMetaDocOutputGenerator(OutputGenerator):
    """Generate specified API interfaces in a specific style, such as a C header"""
    def __init__(self,
                 errFile = sys.stderr,
                 warnFile = sys.stderr,
                 diagFile = sys.stdout):
        OutputGenerator.__init__(self, errFile, warnFile, diagFile)
    #
    def beginFile(self, genOpts):
        OutputGenerator.beginFile(self, genOpts)
    def endFile(self):
        OutputGenerator.endFile(self)
    def beginFeature(self, interface, emit):
        # Start processing in superclass
        OutputGenerator.beginFeature(self, interface, emit)

        # These attributes must exist
        name = interface.get('name')

        if interface.tag != 'extension':
            self.logMsg('diag',
                        'beginFeature: ignoring non-extension feature',
                        name)
            return

        # These attributes are optional
        number = self.getAttrib(interface, 'number', 'UNKNOWN')
        type = self.getAttrib(interface, 'type', None)
        requires = self.getAttrib(interface, 'requires', None)
        contact = self.getAttrib(interface, 'contact', 'UNKNOWN')
        revision = self.getSpecVersion(interface, name, 'UNKNOWN')

        # Create subdirectory, if needed
        directory = self.genOpts.directory
        self.makeDir(directory)

        # Create file
        filename = directory + '/' + name + '.txt'
        self.logMsg('diag', '# Generating include file:', filename)
        fp = open(filename, 'w', encoding='utf-8')

        # Asciidoc anchor
        write('// WARNING: DO NOT MODIFY! This file is automatically generated from the vk.xml registry', file=fp)
        write('[[' + name + ']]', file=fp)
        write('== ' + name, file=fp)
        write('', file=fp)

        write('*Name String*::', file=fp)
        write('    `' + name + '`', file=fp)

        write('*Extension Type*::', file=fp)
        if type == 'instance':
            write('    Instance extension', file=fp)
        elif type == 'device':
            write('    Device extension', file=fp)
        elif type != None:
            write('    UNRECOGNIZED extension type: ' + type, file=fp)
        else:
            self.logMsg('warn',
                        'ExtensionMetaInformation::beginFeature:',
                        'required type attribute missing for extension',
                        name)
            write('    UNKNOWN extension type (*this should never happen*)', file=fp)

        write('*Registered Extension Number*::', file=fp)
        write('    ' + number, file=fp)

        write('*Revision*::', file=fp)
        write('    ' + revision, file=fp)

        # @@ Need to determine *Revision*:: number from enum attributes

        # Only Vulkan extension dependencies are coded in XML, others are explicit
        write('*Extension and Version Dependencies*::', file=fp)
        write('  - Requires Vulkan 1.0', file=fp)
        if requires != None:
            for dep in requires.split(','):
                write('  - Requires `<<' + dep + '>>`', file=fp)

        write('*Contact*::', file=fp)
        write('  - ' + contact, file=fp)

        fp.close()
    def endFeature(self):
        # Finish processing in superclass
        OutputGenerator.endFeature(self)
    #
    # Query an attribute from an element, or return a default value
    #   elem - element to query
    #   attribute - attribute name
    #   default - default value if attribute not present
    def getAttrib(self, elem, attribute, default=None):
        if attribute in elem.keys():
            return elem.get(attribute)
        else:
            return default
    #
    # Determine the extension revision from the EXTENSION_NAME_SPEC_VERSION
    # enumerant.
    #
    #   elem - <extension> element to query
    #   extname - extension name from the <extension> 'name' attribute
    #   default - default value if SPEC_VERSION token not present
    def getSpecVersion(self, elem, extname, default=None):
        # The literal enumerant name to match
        enumName = extname.upper() + '_SPEC_VERSION'
        # A possible revision number if no literal match is found
        specVersion = 'UNKNOWN'

        for enum in elem.findall('.//enum'):
            thisName = enum.get('name')
            thisValue = self.getAttrib(enum, 'value', 'UNKNOWN')
            if thisName == enumName:
                # Exact match
                specVersion = thisValue
                break
            elif thisName[-13:] == '_SPEC_VERSION':
                self.logMsg('diag',
                            'Potential name mismatch between extension',
                            extname, 'and version token', thisName)
                specVersion = thisValue
            # Otherwise, ignore the enum

        if specVersion == 'UNKNOWN':
            print('UNKNOWN SPEC_VERSION for', extname)
        return specVersion
