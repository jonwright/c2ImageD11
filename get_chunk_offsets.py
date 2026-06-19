import h5py
def index_file_2d( h5file, dataset, buffer ):
    # Read the chunk offsets
    with h5py.File( h5file, 'r' ) as hin:
        ds = hin[dataset]
        chunk_infos = np.zeros( ( 3, len(ds) ), int )
        def callback( storeinfo ):
            # StoreInfo(cot, filter_mask, addr, size)
            logical_offset, filter_mask, file_location, size = storeinfo
            chunk_infos[ :, logical_offset[0] ] = filter_mask, file_location, size
        ds.id.chunk_iter( callback )
    return chunk_infos
