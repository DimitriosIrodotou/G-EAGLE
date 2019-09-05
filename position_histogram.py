import re
import time
import warnings

import astropy.units as u
import matplotlib.cbook
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib import gridspec

import eagle_IO.eagle_IO.eagle_IO as E

date = time.strftime('%d_%m_%y_%H%M')  # Date
outdir = '/cosma7/data/dp004/dc-irod1/G-EAGLE/python/plots/'  # Path to save plots.
start_global_time = time.time()  # Start the global time.
warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)


class PositionHistogram:
    """
    A class to create 2 dimensional histograms of the position of stellar particles.

    """


    def __init__(self, sim, tag):
        """
        A constructor method for the class.

        :param sim: simulation directory
        :param tag: redshift folder
        """

        # Load data #
        self.stellar_data, self.subhalo_data = self.read_galaxies(sim, tag)
        print('--- Finished reading the data in %.5s seconds ---' % (time.time() - start_global_time))  # Print reading time.
        print('–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––')

        # Select galaxies with masses above 1e8 Msun #
        mass_mask = np.where(self.subhalo_data['ApertureMeasurements/Mass/030kpc'][:, 4] * u.g.to(u.Msun) > 1e8)
        print('G-EAGLE_' + re.split('GEAGLE_|/data', sim)[2])
        print('Found ' + str(len(list(set(self.subhalo_data['GroupNumber'][mass_mask])))) + ' FOF group(s)')

        # Loop over all distinct GroupNumber #
        for group_number in list(set(self.subhalo_data['GroupNumber'])):
            stellar_data_tmp, galaxy_mask = self.mask_galaxies(group_number)
            if len(galaxy_mask[0]) > 0.0:

                # Plot data #
                start_local_time = time.time()  # Start the local time.
                self.plot(stellar_data_tmp, group_number)
                print('--- Finished plotting the data in %.5s seconds ---' % (time.time() - start_local_time))  # Print plotting time.
            print('–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––')
        print('--- Finished PositionHistogram.py in %.5s seconds ---' % (time.time() - start_global_time))  # Print total time.
        print('–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––')


    # Loop over all distinct SubGroupNumber #
    # for subgroup_number in list(set(self.subhalo_data['SubGroupNumber'])):

    # Find the index of where the new FOF begins #
    # index = np.where(self.subhalo_data['SubGroupNumber'] == 0)
    # for group_number in range(len(index[0])):

    @staticmethod
    def read_galaxies(sim, tag):
        """
         A method to extract particle and subhalo properties and convert them to h-free physical CGS units.

        :param sim: simulation directory
        :param tag: redshift folder
        :return: stellar_data, subhalo_data
        """

        # Load subhalo data #
        subhalo_data = {}
        file_type = 'SUBFIND'
        for properties in ['GroupNumber', 'SubGroupNumber', 'CentreOfPotential', 'ApertureMeasurements/Mass/030kpc']:
            subhalo_data[properties] = E.read_array(file_type, sim, tag, '/Subhalo/' + properties, numThreads=4)

        # Load particle data #
        stellar_data = {}
        particle_type = '4'
        file_type = 'PARTDATA'
        for properties in ['GroupNumber', 'SubGroupNumber', 'Coordinates']:
            stellar_data[properties] = E.read_array(file_type, sim, tag, '/PartType' + particle_type + '/' + properties, numThreads=4)

        # Convert to astronomical units #
        stellar_data['Coordinates'] *= u.cm.to(u.kpc)
        subhalo_data['CentreOfPotential'] *= u.cm.to(u.kpc)

        return stellar_data, subhalo_data


    def mask_galaxies(self, group_number):
        """
        A method to select galaxies.

        :return: galaxy_mask
        """
        mass_mask = np.where(self.subhalo_data['ApertureMeasurements/Mass/030kpc'][:, 4] * u.g.to(u.Msun) > 1e8)
        index = (np.where(self.subhalo_data['SubGroupNumber'][mass_mask] == 0))[0][group_number-1]
        print(index)

        # Mask data to select galaxies and particles inside a 30kpc sphere #
        galaxy_mask = np.where((self.stellar_data['GroupNumber'] == group_number) & (self.stellar_data['SubGroupNumber'] == 0) & (
            np.sqrt(np.sum((self.stellar_data['Coordinates'] - self.subhalo_data['CentreOfPotential'][group_number-1]) ** 2, axis=1)) <= 30.0))

        # Store the temporary data #
        stellar_data_tmp = {}
        for properties in self.stellar_data.keys():
            stellar_data_tmp[properties] = np.copy(self.stellar_data[properties])[galaxy_mask]

        # Normalise the coordinates wr t the centre of potential of the subhalo #
        stellar_data_tmp['Coordinates'] = np.subtract(stellar_data_tmp['Coordinates'], self.subhalo_data['CentreOfPotential'][group_number-1])

        return stellar_data_tmp, galaxy_mask


    @staticmethod
    def plot(stellar_data_tmp, group_number):
        """
        A method to plot a hexbin histogram.

        :param stellar_data_tmp: temporary data
        :param group_number: list(set(self.subhalo_data['GroupNumber']))
        :return: None
        """

        # Set the style of the plots #
        sns.set()
        sns.set_style('ticks')
        sns.set_context('notebook', font_scale=1.6)

        # Generate the figures #
        plt.close()
        figure = plt.figure(0, figsize=(10, 10))

        gs = gridspec.GridSpec(2, 2, height_ratios=[2, 1], width_ratios=(20, 1))
        gs.update(hspace=0.2)
        axtop = plt.subplot(gs[0, 0])
        axbot = plt.subplot(gs[1, 0])
        axcbar = plt.subplot(gs[:, 1])

        # Generate the XY projection #
        # axtop.set_xlim(-5, 5)
        # axtop.set_ylim(-5, 5)
        axtop.set_xlabel(r'$\mathrm{x/kpc}$')
        axtop.set_ylabel(r'$\mathrm{y/kpc}$')
        axtop.tick_params(direction='in', which='both', top='on', right='on')
        axtop.set_facecolor('k')

        pltop = axtop.hexbin(list(zip(*stellar_data_tmp['Coordinates']))[0], list(zip(*stellar_data_tmp['Coordinates']))[1], bins='log', cmap='bone',
                             gridsize=50, edgecolor='none')

        # Generate the XZ projection #
        # axbot.set_xlim(-5, 5)
        # axbot.set_ylim(-5, 5)
        axbot.set_xlabel(r'$\mathrm{x/kpc}$')
        axbot.set_ylabel(r'$\mathrm{z/kpc}$')
        axbot.set_facecolor('k')
        plbot = axbot.hexbin(list(zip(*stellar_data_tmp['Coordinates']))[0], list(zip(*stellar_data_tmp['Coordinates']))[2], bins='log', cmap='bone',
                             gridsize=50, edgecolor='none')

        # Generate the color bar #
        cbar = plt.colorbar(pltop, cax=axcbar)
        cbar.set_label('$\mathrm{log_{10}(Particles\; per\; hexbin)}$')

        # Save the plot #
        plt.title('z ~ ' + re.split('_z0|p000', tag)[1])
        plt.savefig(outdir + 'PH' + '-' + str(group_number) + '-' + date + '.png', bbox_inches='tight')

        return None


if __name__ == '__main__':
    tag = '010_z005p000'
    sim = '/cosma7/data/dp004/dc-payy1/G-EAGLE/GEAGLE_06/data/'
    x = PositionHistogram(sim, tag)