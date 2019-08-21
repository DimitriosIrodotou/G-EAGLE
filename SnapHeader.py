import h5py


def read_header():
    # Read various attributes from the header group
    f = h5py.File('/Users/Bam/PycharmProjects/G-EAGLE/G-EAGLE_Data/0021/particledata_007_z008p000/eagle_subfind_particles_007_z008p000.0.hdf5', 'r')
    a = f['Header'].attrs.get('Time')  # Scale factor.
    h = f['Header'].attrs.get('HubbleParam')  # h.
    boxsize = f['Header'].attrs.get('BoxSize')  # L [Mph/h].
    f.close()
    return a, h, boxsize