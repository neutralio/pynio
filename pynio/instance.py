from copy import deepcopy
from pynio.rest import REST
from pynio.block import Block
from pynio.service import Service


class Instance(REST):
    """ Interface for a running n.io instance.

    This is the main part of pynio. All communication with the n.io instance
    goes through this object. Blocks and Services contain a reference to an
    Instance in order to communication with the running instance.

    Args:
        host (str, optional): Host ip address of running n.io instance.
            Default is '127.0.0.1'.
        port (int, optional): Port of runing n.io instance. Default is 8181.
        creds ((str, str), optional): Username and password for basic
            authentication. Default is ('Admin', 'Admin').
    """

    def __init__(self, host='127.0.0.1', port=8181, creds=None):
        super().__init__(host, port, creds)
        self.droplog = print
        self.blocks_types = {}
        self.blocks = {}
        self.services = {}
        # reset to initalize instance
        self.reset()

    def reset(self):
        self.blocks_types, self.blocks = self._get_blocks()
        self.services = self._get_services()

    def nio(self):
        """ Returns nio version info.

        """
        return self._get('nio')

    def add_block(self, block):
        block._instance = self
        block.save()
        return block

    def add_service(self, service):
        service._instance = self
        service.save()
        return service

    def _get_blocks(self):
        blocks_types = {}
        for btype, template in self._get('blocks_types').items():
            b = Block(btype, btype, instance=self)
            b._load_template(btype, template)
            blocks_types[btype] = b

        blocks = {}
        for bname, config in self._get('blocks').items():
            btype = config['type']
            b = blocks_types[btype].copy(bname, instance=self)
            b.config = config
            blocks[bname] = b

        return blocks_types, blocks

    def _get_services(self):
        services = {}
        resp = self._get('services')
        for s in resp:
            services[s] = Service(resp[s].get('name'),
                                  config=resp[s],
                                  instance=self)
        return services

    def create_block(self, name, type, config=None):
        '''Convenience function to create a block and add it to instance'''
        block = Block(name, type, config, instance=self)
        block.save()
        return block

    def create_service(self, name, type=None, config=None):
        '''Convenience function to create a service and add it to instance'''
        if type is None:
            service = Service(name, config=config, instance=self)
        else:
            service = Service(name, type, config=config, instance=self)
        service.save()
        return service

    def DELETE_ALL(self):
        '''Deletes all blocks and services from an instance
        regardless of whether or not they can be loaded. Does a reset after
        '''
        blocks, services = self._get('blocks'), self._get('services')
        for b in blocks:
            self._delete('blocks/{}'.format(b))
        for s in services:
            self._get('services/{}/stop'.format(s))
            self._delete('services/{}'.format(s))
        self.reset()

    def copy_block(self, block, overwrite=False):
        '''Copy block from another instance to self.'''
        if not overwrite and block.name in self.blocks:
            raise ValueError
        return self.add_block(deepcopy(block))

    def copy_service(self, service, overwrite=False):
        '''Copy service from another instance to self.'''
        blocks = service.blocks
        if not overwrite:
            if service.name in self.services:
                raise ValueError("Service already exists {}".
                                    format(service.name))
            # make sure no blocks have the same name
            bnames = {b.name for b in blocks}
            mybnames = set(self.blocks.keys())
            intersect = bnames.intersection(mybnames)
            if intersect:
                raise ValueError(
                    "Some blocks from service {} already exist: {}".
                    format(service.name, intersect))
        out_blocks = [self.copy_block(b, True) for b in blocks]
        out_service = self.add_service(deepcopy(service))
        return out_service, out_blocks
