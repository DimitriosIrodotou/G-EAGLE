import re
import time
import warnings
import argparse
import matplotlib

matplotlib.use('Agg')

import numpy as np
import seaborn as sns
import matplotlib.cbook
import astropy.units as u
import matplotlib.pyplot as plt
import eagle_IO.eagle_IO.eagle_IO as E

from matplotlib import gridspec

# Create a parser and add argument to read data #
parser = argparse.ArgumentParser(description='Create 2 dimensional histograms of the position of stellar particles.')
parser.add_argument('-r', action='store_true', help='Read data')
parser.add_argument('-l', action='store_true', help='Load data')
parser.add_argument('-rs', action='store_true', help='Read data and save to numpy arrays')
args = parser.parse_args()

date = time.strftime('%d_%m_%y_%H%M')  # Date
start_global_time = time.time()  # Start the global time.
warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)  # Ignore some plt warnings.


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
        
        p = 1  # Counter.
        stellar_data_tmp = {}  # Initialise a dictionary to store the data.
        
        if not args.l:
            self.Ngroups = E.read_header('SUBFIND', sim, tag, 'TotNgroups')
            self.stellar_data, self.subhalo_data = self.read_galaxies(sim, tag)
            print('Read data for ' + re.split('G-EAGLE/|/data', sim)[2] + ' in %.4s s' % (time.time() - start_global_time))
            print('–––––––––––––––––––––––––––––––––––––––––')
            
            self.subhalo_data_tmp = self.mask_haloes()  # Mask haloes to select only those with stellar mass > 10^8Msun.
        
        # for group_number in list(set(self.subhalo_data_tmp['GroupNumber'])):  # Loop over all the accepted haloes
        for group_number in range(1, 21):  # Loop over all the accepted haloes
            for subgroup_number in range(0, 1):
                if args.rs:  # Read and save data.
                    start_local_time = time.time()  # Start the local time.
                    
                    stellar_data_tmp = self.mask_galaxies(group_number, subgroup_number)  # Mask the data
                    
                    # Save data in nampy arrays #
                    np.save(SavePath + 'group_number_' + str(group_number), group_number)
                    np.save(SavePath + 'subgroup_number_' + str(group_number), subgroup_number)
                    np.save(SavePath + 'stellar_data_tmp_' + str(group_number), stellar_data_tmp)
                    print('Masked and saved data for halo ' + str(group_number) + ' in %.4s s' % (time.time() - start_local_time) + ' (' + str(
                        round(100 * p / len(set(self.subhalo_data_tmp['GroupNumber'])), 1)) + '%)')
                    print('–––––––––––––––––––––––––––––––––––––––––––––')
                    p += 1
                
                elif args.r:  # Read data.
                    start_local_time = time.time()  # Start the local time.
                    
                    stellar_data_tmp = self.mask_galaxies(group_number, subgroup_number)  # Mask the data
                    print('Masked data for halo ' + str(group_number) + ' in %.4s s' % (time.time() - start_local_time) + ' (' + str(
                        round(100 * p / len(set(self.subhalo_data_tmp['GroupNumber'])), 1)) + '%)')
                    print('–––––––––––––––––––––––––––––––––––––––––––––')
                    p += 1
                
                elif args.l:  # Load data.
                    start_local_time = time.time()  # Start the local time.
                    
                    group_number = np.load(SavePath + 'group_number_' + str(group_number) + '.npy')
                    subgroup_number = np.load(SavePath + 'subgroup_number_' + str(group_number) + '.npy')
                    stellar_data_tmp = np.load(SavePath + 'stellar_data_tmp_' + str(group_number) + '.npy', allow_pickle=True)
                    stellar_data_tmp = stellar_data_tmp.item()
                    print('Loaded data for halo ' + str(group_number) + ' in %.4s s' % (time.time() - start_local_time))
                    # + ' (' + str(round(100 * p / len(set(self.subhalo_data_tmp['GroupNumber'])), 1)) + '%)')
                    print('–––––––––––––––––––––––––––––––––––––––––––––')
                
                # Plot the data #
                start_local_time = time.time()  # Start the local time.
                
                self.plot(stellar_data_tmp, group_number, subgroup_number)
                print('Plotted data for halo ' + str(group_number) + ' in %.4s s' % (time.time() - start_local_time))
                print('–––––––––––––––––––––––––––––––––––––––––')
        
        print('Finished PositionHistogram for ' + re.split('G-EAGLE/|/data', sim)[2] + ' in %.4s s' % (
            time.time() - start_global_time))  # Print total time.
        print('–––––––––––––––––––––––––––––––––––––––––')
    
    
    @staticmethod
    def read_galaxies(sim, tag):
        """
         A static method to extract particle and subhalo attribute.
        :param sim: simulation directory
        :param tag: redshift folder
        :return: stellar_data, subhalo_data
        """
        
        # Load subhalo data in h-free physical CGS units #
        subhalo_data = {}
        file_type = 'SUBFIND'
        for attribute in ['ApertureMeasurements/Mass/030kpc', 'CentreOfPotential', 'GroupNumber', 'SubGroupNumber']:
            subhalo_data[attribute] = E.read_array(file_type, sim, tag, '/Subhalo/' + attribute, numThreads=8)
        
        # Load particle data in h-free physical CGS units #
        stellar_data = {}
        particle_type = '4'
        file_type = 'PARTDATA'
        for attribute in ['Coordinates', 'GroupNumber', 'SubGroupNumber']:
            stellar_data[attribute] = E.read_array(file_type, sim, tag, '/PartType' + particle_type + '/' + attribute, numThreads=8)
        
        # Convert to astronomical units #
        stellar_data['Coordinates'] *= u.cm.to(u.kpc)
        subhalo_data['CentreOfPotential'] *= u.cm.to(u.kpc)
        subhalo_data['ApertureMeasurements/Mass/030kpc'] *= u.g.to(u.Msun)
        
        return stellar_data, subhalo_data
    
    
    def mask_haloes(self):
        """
        A method to mask haloes.
        :return: subhalo_data_tmp
        """
        
        # Mask the data to select haloes more #
        mask = np.where(self.subhalo_data['ApertureMeasurements/Mass/030kpc'][:, 4] > 1e8)
        
        # Mask the temporary dictionary for each galaxy #
        subhalo_data_tmp = {}
        for attribute in self.subhalo_data.keys():
            subhalo_data_tmp[attribute] = np.copy(self.subhalo_data[attribute])[mask]
        
        return subhalo_data_tmp
    
    
    def mask_galaxies(self, group_number, subgroup_number):
        """
        A method to mask galaxies.
        :param group_number: from list(set(self.subhalo_data_tmp['GroupNumber']))
        :param subgroup_number: from list(set(self.subhalo_data_tmp['SubGroupNumber']))
        :return: stellar_data_tmp
        """
        
        # Select the corresponding halo in order to get its centre of potential #
        index = np.where(self.subhalo_data_tmp['GroupNumber'] == group_number)[0][subgroup_number]
        
        # Mask the data to select galaxies with a given GroupNumber and SubGroupNumber and particles inside a 30kpc sphere #
        mask = np.where((self.stellar_data['GroupNumber'] == group_number) & (self.stellar_data['SubGroupNumber'] == subgroup_number) & (
            np.linalg.norm(np.subtract(self.stellar_data['Coordinates'], self.subhalo_data_tmp['CentreOfPotential'][index]), axis=1) <= 30.0) & (
                            self.subhalo_data_tmp['ApertureMeasurements/Mass/030kpc'][:, 4][index] > 1e8))
        
        # Mask the temporary dictionary for each galaxy #
        stellar_data_tmp = {}
        for attribute in self.stellar_data.keys():
            stellar_data_tmp[attribute] = np.copy(self.stellar_data[attribute][mask])
        
        # Normalise the coordinates wrt the centre of potential of the subhalo #
        stellar_data_tmp['Coordinates'] = np.subtract(stellar_data_tmp['Coordinates'], self.subhalo_data_tmp['CentreOfPotential'][index])
        
        return stellar_data_tmp
    
    
    @staticmethod
    def plot(stellar_data_tmp, group_number, subgroup_number):
        """
        A method to plot a hexbin histogram.
        :param stellar_data_tmp: temporary data
        :param group_number: from list(set(self.subhalo_data_tmp['GroupNumber']))
        :param subgroup_number: from list(set(self.subhalo_data_tmp['SubGroupNumber']))
        :return: None
        """
        
        # Set the style of the plots #
        sns.set()
        sns.set_style('ticks')
        sns.set_context('notebook', font_scale=1.6)
        
        # Generate the figures #
        plt.close()
        figure = plt.figure(0, figsize=(20, 7.5))
        
        gs = gridspec.GridSpec(2, 3, height_ratios=(0.03, 1))
        gs.update(hspace=0.4, wspace=0.3)
        axleft = plt.subplot(gs[1, 0])
        axmid = plt.subplot(gs[1, 1])
        axright = plt.subplot(gs[1, 2])
        axcbar1 = plt.subplot(gs[0, 0])
        axcbar2 = plt.subplot(gs[0, 1])
        axcbar3 = plt.subplot(gs[0, 2])
        
        # Generate the XY projection #
        axleft.set_xlim(-10, 10)
        axleft.set_ylim(-10, 10)
        axleft.set_xlabel(r'$\mathrm{x/kpc}$')
        axleft.set_ylabel(r'$\mathrm{y/kpc}$')
        axleft.tick_params(direction='in', which='both', top='on', right='on')
        axleft.set_facecolor('k')
        plleft = axleft.hexbin(list(zip(*stellar_data_tmp['Coordinates']))[0], list(zip(*stellar_data_tmp['Coordinates']))[1], bins='log',
                               cmap='bone', gridsize=300, edgecolor='none')
        
        # Generate the XZ projection #
        axmid.set_xlim(-10, 10)
        axmid.set_ylim(-10, 10)
        axmid.set_xlabel(r'$\mathrm{x/kpc}$')
        axmid.set_ylabel(r'$\mathrm{z/kpc}$')
        axmid.set_facecolor('k')
        plmid = axmid.hexbin(list(zip(*stellar_data_tmp['Coordinates']))[0], list(zip(*stellar_data_tmp['Coordinates']))[2], bins='log', cmap='bone',
                             gridsize=300, edgecolor='none')
        
        # Generate the ZY projection #
        axright.set_xlim(-10, 10)
        axright.set_ylim(-10, 10)
        axright.set_xlabel(r'$\mathrm{y/kpc}$')
        axright.set_ylabel(r'$\mathrm{z/kpc}$')
        axright.set_facecolor('k')
        plright = axright.hexbin(list(zip(*stellar_data_tmp['Coordinates']))[1], list(zip(*stellar_data_tmp['Coordinates']))[2], bins='log',
                                 cmap='bone', gridsize=300, edgecolor='none')
        
        # Generate the color bar #
        cbar1 = plt.colorbar(plleft, cax=axcbar1, orientation='horizontal')
        cbar1.set_label('$\mathrm{Particles\; per\; hexbin}$')
        cbar2 = plt.colorbar(plmid, cax=axcbar2, orientation='horizontal')
        cbar2.set_label('$\mathrm{Particles\; per\; hexbin}$')
        cbar3 = plt.colorbar(plright, cax=axcbar3, orientation='horizontal')
        cbar3.set_label('$\mathrm{Particles\; per\; hexbin}$')
        
        # Save the plot #
        plt.title('z ~ ' + re.split('_z0|p000', tag)[1])
        plt.savefig(outdir + str(group_number) + str(subgroup_number) + '-' + 'PH' + '-' + date + '.png', bbox_inches='tight')
        
        return None


if __name__ == '__main__':
    tag = '010_z005p000'
    sim = '/cosma7/data/dp004/dc-payy1/G-EAGLE/GEAGLE_06/data/'
    outdir = '/cosma7/data/dp004/dc-irod1/G-EAGLE/python/plots/PH/G-EAGLE/'  # Path to save plots.
    SavePath = '/cosma7/data/dp004/dc-irod1/G-EAGLE/python/data/PH/G-EAGLE/'  # Path to save/load data.
    # tag = '027_z000p101'
    # sim = '/cosma5/data/Eagle/ScienceRuns/Planck1/L0100N1504/PE/REFERENCE/data/'
    # outdir = '/cosma7/data/dp004/dc-irod1/G-EAGLE/python/plots/PH/EAGLE/'  # Path to save plots.
    # SavePath = '/cosma7/data/dp004/dc-irod1/G-EAGLE/python/data/PH/EAGLE/'  # Path to save/load data.
    x = PositionHistogram(sim, tag)