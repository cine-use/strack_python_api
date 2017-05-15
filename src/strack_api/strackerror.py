# coding=utf8
# Copyright (c) 2016 Strack
import sys
import traceback


class StrackError(Exception):
    '''Base for FTrack specific errors.'''

    defaultMessage = 'Unspecified error'

    def __init__(self, message=None, details=None, **kw):
        '''Initialise exception with *message*.

        If *message* is None, the class 'defaultMessage' will be used.

        '''
        if not message:
            message = self.defaultMessage

        self.message = message.encode("utf-8")
        self.details = details
        self.traceback = traceback.format_exc()

    # def __str__(self):
    #     keys = {}
    #     for key, value in self.__dict__.iteritems():
    #         if isinstance(value, unicode):
    #             value = value.encode(sys.getfilesystemencoding())
    #         keys[key] = value
    #
    #     return str(self.message.format(**keys))

    def __str__(self):
        return self.message

class PermissionDeniedError(StrackError):
    '''Raise when permission is denied.'''

    defaultMessage = 'Permission denied.'


class LocationError(StrackError):
    '''Base for errors associated with locations.'''

    defaultMessage = 'Unspecified location error'


class ComponentNotInAnyLocationError(LocationError):
    '''Raise when component not available in any location.'''

    defaultMessage = 'Component not available in any location.'


class ComponentNotInLocationError(LocationError):
    '''Raise when component(s) not in location.'''

    def __init__(self, componentIds, locationId, **kw):
        '''Initialise with *componentIds* and *locationId*.'''
        self.componentIds = '"{0}"'.format('", "'.join(componentIds))
        self._missingIds = componentIds
        self.locationId = locationId
        super(ComponentNotInLocationError, self).__init__(**kw)

    def getMissingIds(self):
        '''Return a list of components missing in the location.'''
        return self._missingIds

    defaultMessage = (
        'Component(s) {componentIds} not found in location "{locationId}".'
    )


class ComponentInLocationError(LocationError):
    '''Raise when component already exists in location.'''

    def __init__(self, componentId, locationId, **kw):
        '''Initialise with *componentId* and *locationId*.'''
        self.componentId = componentId
        self.locationId = locationId
        super(ComponentInLocationError, self).__init__(**kw)

    defaultMessage = (
        'Component "{componentId}" already exists in location "{locationId}".'
    )


class AccessorError(StrackError):
    '''Base for errors associated with accessors.'''

    defaultMessage = 'Unspecified accessor error'


class AccessorOperationFailedError(AccessorError):
    '''Base for failed operations on accessors.'''

    defaultMessage = 'Operation {operation} failed: {details}'

    def __init__(self, operation='', resourceIdentifier=None, **kw):
        self.operation = operation
        self.resourceIdentifier = resourceIdentifier
        super(AccessorOperationFailedError, self).__init__(**kw)


class AccessorUnsupportedOperationError(AccessorOperationFailedError):
    '''Raise when operation is unsupported.'''

    defaultMessage = 'Operation {operation} unsupported.'


class AccessorPermissionDeniedError(AccessorOperationFailedError):
    '''Raise when permission denied.'''

    defaultMessage = ('Cannot {operation} {resourceIdentifier}. '
                      'Permission denied.')


class AccessorResourceIdentifierError(AccessorError):
    '''Raise when a error related to a resourceIdentifier occurs.'''

    defaultMessage = 'Resource identifier is invalid: {resourceIdentifier}.'

    def __init__(self, resourceIdentifier, **kw):
        self.resourceIdentifier = resourceIdentifier
        super(AccessorResourceIdentifierError, self).__init__(**kw)


class AccessorFilesystemPathError(AccessorResourceIdentifierError):
    '''Raise when a error related to an accessor filesystem path occurs.'''

    defaultMessage = ('Could not determine filesystem path from resource '
                      'identifier: {resourceIdentifier}.')


class AccessorResourceError(AccessorError):
    '''Base for errors associated with specific resource.'''

    defaultMessage = 'Unspecified resource error: {resourceIdentifier}'

    def __init__(self, resourceIdentifier, **kw):
        self.resourceIdentifier = resourceIdentifier
        super(AccessorResourceError, self).__init__(**kw)


class AccessorResourceNotFoundError(AccessorResourceError):
    '''Raise when a required resource is not found.'''

    defaultMessage = 'Resource not found: {resourceIdentifier}'


class AccessorParentResourceNotFoundError(AccessorResourceError):
    '''Raise when a parent resource (such as directory) is not found.'''

    defaultMessage = 'Parent resource is missing: {resourceIdentifier}'


class AccessorResourceInvalidError(AccessorResourceError):
    '''Raise when a resource is not the right type.'''

    defaultMessage = 'Resource invalid: {resourceIdentifier}'


class AccessorContainerNotEmptyError(AccessorResourceError):
    '''Raise when container is not empty.'''

    defaultMessage = 'Container is not empty: {resourceIdentifier}'


class EventHubError(StrackError):
    '''Raise when issues related to event hub occur.'''

    defaultMessage = 'Event hub error occurred.'


class EventHubConnectionError(EventHubError):
    '''Raise when event hub encounters connection problem.'''

    defaultMessage = 'Event hub is not connected.'


class EventHubPacketError(EventHubError):
    '''Raise when event hub encounters an issue with a packet.'''

    defaultMessage = 'Invalid packet.'


class NotUniqueError(StrackError):
    '''Raise when something that should be unique is not.'''

    defaultMessage = 'Not unique.'


class NotFoundError(StrackError):
    '''Raise when something that should exist is not found.'''

    defaultMessage = 'Not found.'


class ParseError(StrackError):
    '''Raise when a parsing error occurs.'''

    defaultMessage = 'Failed to parse.'
