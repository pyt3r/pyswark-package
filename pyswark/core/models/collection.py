from typing import Any, Union
from pydantic import field_validator
from pyswark.lib.pydantic import base, ser_des
from pyswark.core.models import extractor, primitive



class Base( extractor.Extractor ):
    inputs: Any

    def __init__(self, inputs):
        return super().__init__( inputs=inputs )

    @field_validator( 'inputs' )
    def _inputs( cls, inputs ) -> list:
        new = []
        for i, e in enumerate( inputs ):
            element = e

            if isinstance( element, base.BaseModel ):
                element = e.toDict()

            elif isinstance( element, dict ) and ser_des.isSerializedDict( element ):
                element = element

            elif Infer.inScope( element ):
                element = Infer( element ).toDict()

            elif primitive.Infer.inScope( element ):
                element = primitive.Infer( element ).toDict()

            else:
                raise ValueError( f"Cannot handle {type(element)} for data[{i}]" )

            new.append( element )
        return new

    def extractModels(self):
        return [ ser_des.fromDict(e) for e in self.inputs ]

    def extract(self):
        data = []
        for e in self.extractModels():
            model = e
            if isinstance( model, ( Base, primitive.Base )):
                model = model.extract()
            data.append( model )
        return data


class List( Base ):
    inputs: Union[ list, tuple ]


class Tuple( List ):

    def extract(self):
        return tuple( super().extract() )


class Set( List ):

    def __init__(self, inputs):
        if isinstance( inputs, set ):
            inputs = list( inputs )
        return super().__init__( inputs=inputs )

    def extract(self):
        return set( super().extract() )


class Dict( List ):
    inputs: Union[ dict, list ]

    @field_validator( 'inputs' )
    def _inputs( cls, inputs ) -> list:

        if isinstance( inputs, dict ):
            inputs = list( inputs.items() )

        cls._validateLengths( inputs )
        inputs = super()._inputs( inputs )

        cls._validateKeys( inputs )

        return inputs

    @staticmethod
    def _validateLengths( inputs ):
        for i, e in enumerate(inputs):
            if len(e) != 2:
                raise ValueError( f"inputs[{i}] must have a length of 2, got {len(e)} for " )

    @staticmethod
    def _validateKeys( inputs ):
        keys = set()
        for key, _ in inputs:
            if key in keys:
                raise ValueError(f"duplicate keys for {key=}")

    def extract(self):
        return dict( super().extract() )

class Infer( primitive.Infer ):

    TYPE_MAP = {
        list  : List,
        tuple : Tuple,
        set   : Set,
        dict  : Dict,
    }


