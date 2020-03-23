import os
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
from astropy_healpix import HEALPix
from rotate_galaxies import RotateCoordinates
from morpho_kinematics import MorphoKinematics

# Create a parser and add argument to read data #
parser = argparse.ArgumentParser(description='Create D/T vs kappa_rot plot.')
parser.add_argument('-r', action='store_true', help='Read data')
parser.add_argument('-l', action='store_true', help='Load data')
parser.add_argument('-rs', action='store_true', help='Read data and save to numpy arrays')
args = parser.parse_args()

date = time.strftime('%d_%m_%y_%H%M')  # Date
start_global_time = time.time()  # Start the global time.
warnings.filterwarnings('ignore', category=matplotlib.cbook.mplDeprecation)  # Ignore some plt warnings.


class DiscToTotalProbabilityDensityFunction:
    """
    Create a disc to total ratio as a function of stellar mass.
    """
    
    
    def __init__(self, simulation_path, tag):
        """
        A constructor method for the class.
        :param simulation_path: simulation directory
        :param tag: redshift folder
        """
        
        p = 1  # Counter.
        # Initialise empty arrays to hold the data #
        kappas, glx_masses, disc_fractions, disc_fractions_IT20 = [], [], [], []
        
        if not args.l:
            # Extract particle and subhalo attributes and convert them to astronomical units #
            self.stellar_data, self.subhalo_data = self.read_galaxies(simulation_path, tag)
            print('Read data for ' + re.split('EAGLE/|/data', simulation_path)[2] + ' in %.4s s' % (time.time() - start_global_time))
            print('–––––––––––––––––––––––––––––––––––––––––')
            
            self.subhalo_data_tmp = self.mask_haloes()  # Mask haloes to select only those with stellar mass > 10^8Msun.
            
            for group_number in np.sort(list(set(self.subhalo_data_tmp['GroupNumber']))):  # Loop over all the accepted haloes
                for subgroup_number in range(0, 1):
                    if args.rs:  # Read and save data.
                        start_local_time = time.time()  # Start the local time.
                        
                        kappa, disc_fraction, disc_fraction_IT20, glx_mass = self.mask_galaxies(group_number, subgroup_number)  # Mask the data.
                        
                        # Save data in numpy arrays #
                        np.save(data_path + 'kappa_' + str(group_number), kappa)
                        np.save(data_path + 'disc_fraction_' + str(group_number), disc_fraction)
                        np.save(data_path + 'glx_masses/' + 'glx_mass_' + str(group_number), glx_mass)
                        np.save(data_path + 'disc_fraction_IT20_' + str(group_number), disc_fraction_IT20)
                        print('Masked and saved data for halo ' + str(group_number) + ' in %.4s s' % (time.time() - start_local_time) + ' (' + str(
                            round(100 * p / len(set(self.subhalo_data_tmp['GroupNumber'])), 1)) + '%)')
                        print('–––––––––––––––––––––––––––––––––––––––––––––')
                        p += 1
                    elif args.r:  # Read data.
                        start_local_time = time.time()  # Start the local time.
                        
                        kappa, disc_fraction, disc_fraction_IT20, glx_mass = self.mask_galaxies(group_number, subgroup_number)  # Mask the data.
                        kappas.append(kappa)
                        glx_masses.append(glx_mass)
                        disc_fractions.append(disc_fraction)
                        disc_fractions_IT20.append(disc_fraction_IT20)
                        print('Masked data for halo ' + str(group_number) + ' in %.4s s' % (time.time() - start_local_time) + ' (' + str(
                            round(100 * p / len(set(self.subhalo_data_tmp['GroupNumber'])), 1)) + '%)')
                        print('–––––––––––––––––––––––––––––––––––––––––––––')
                        p += 1  # Increase the count by one.
                    
                    if args.l or args.rs:  # Load data.
                        start_local_time = time.time()  # Start the local time.
                        
                        # kappa = np.load(data_path + 'kappa_' + str(group_number) + '.npy')
                        glx_mass = np.load(data_path + 'glx_masses/' + 'glx_mass_' + str(group_number) + '.npy')
                        # disc_fraction = np.load(data_path + 'disc_fraction_' + str(group_number) + '.npy')
                        # disc_fraction_IT20 = np.load(data_path + 'disc_fraction_IT20_' + str(group_number) + '.npy')
                        # kappas.append(kappa.item())
                        glx_masses.append(glx_mass.item())
                        # disc_fractions.append(disc_fraction.item())
                        # disc_fractions_IT20.append(disc_fraction_IT20.item())
                        print('Loaded data for halo ' + str(group_number) + ' in %.4s s' % (time.time() - start_local_time))
                        # + ' (' + str(round(100 * p / len(set(self.subhalo_data_tmp['GroupNumber'])), 1)) + '%)')
                        print('–––––––––––––––––––––––––––––––––––––––––––––')
            
            if args.l or args.rs:  # Load data.
                # np.save(data_path + 'kappas', kappas)
                np.save(data_path + 'glx_masses/' + 'glx_masses',
                        glx_masses)  # np.save(data_path + 'disc_fractions', disc_fractions)  # np.save(data_path + 'disc_fractions_IT20',
                # disc_fractions_IT20)
        else:
            start_local_time = time.time()  # Start the local time.
            
            kappas = np.load(data_path + 'kappas/' + 'kappas.npy')
            glx_masses = np.load(data_path + 'glx_masses/' + 'glx_masses.npy')
            disc_fractions = np.load(data_path + 'disc_fractions/' + 'disc_fractions.npy')
            disc_fractions_IT20 = np.load(data_path + 'disc_fractions_IT20/' + 'disc_fractions_IT20.npy')
            print('Loaded data for ' + re.split('EAGLE/|/data', simulation_path)[0] + ' in %.4s s' % (time.time() - start_local_time))
            print('–––––––––––––––––––––––––––––––––––––––––')
        
        # Plot the data #
        start_local_time = time.time()  # Start the local time.
        
        self.plot(kappas, disc_fractions, disc_fractions_IT20, glx_masses)
        print('Plotted data for ' + re.split('EAGLE/|/data', simulation_path)[2] + ' in %.4s s' % (time.time() - start_local_time))
        print('–––––––––––––––––––––––––––––––––––––––––––––')
        
        print('Finished DTTM for ' + re.split('EAGLE/|/data', simulation_path)[2] + ' in %.4s s' % (time.time() - start_global_time))
        print('–––––––––––––––––––––––––––––––––––––––––––––')
    
    
    @staticmethod
    def read_galaxies(simulation_path, tag):
        """
        Extract particle and subhalo attributes and convert them to astronomical units.
        :param simulation_path: simulation directory
        :param tag: redshift folder
        :return: stellar_data, subhalo_data
        """
        
        # Load subhalo data in h-free physical CGS units #
        subhalo_data = {}
        file_type = 'SUBFIND'
        for attribute in ['ApertureMeasurements/Mass/030kpc', 'CentreOfPotential', 'GroupNumber', 'SubGroupNumber']:
            subhalo_data[attribute] = E.read_array(file_type, simulation_path, tag, '/Subhalo/' + attribute, numThreads=8)
        
        # Load particle data in h-free physical CGS units #
        stellar_data = {}
        particle_type = '4'
        file_type = 'PARTDATA'
        for attribute in ['Coordinates', 'GroupNumber', 'Mass', 'ParticleBindingEnergy', 'SubGroupNumber', 'Velocity']:
            stellar_data[attribute] = E.read_array(file_type, simulation_path, tag, '/PartType' + particle_type + '/' + attribute, numThreads=8)
        
        # Convert attributes to astronomical units #
        stellar_data['Mass'] *= u.g.to(u.Msun)
        stellar_data['Velocity'] *= u.cm.to(u.km)  # per second.
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
        halo_mask = np.where(self.subhalo_data['ApertureMeasurements/Mass/030kpc'][:, 4] > 1e8)
        
        # Mask the temporary dictionary for each galaxy #
        subhalo_data_tmp = {}
        for attribute in self.subhalo_data.keys():
            subhalo_data_tmp[attribute] = np.copy(self.subhalo_data[attribute])[halo_mask]
        
        return subhalo_data_tmp
    
    
    def mask_galaxies(self, group_number, subgroup_number):
        """
        A method to mask galaxies.
        :param group_number: from list(set(self.subhalo_data_tmp['GroupNumber']))
        :param subgroup_number: from list(set(self.subhalo_data_tmp['SubGroupNumber']))
        :return: stellar_data_tmp, prc_unit_vector
        """
        
        # Select the corresponding halo in order to get its centre of potential #
        halo_mask = np.where(self.subhalo_data_tmp['GroupNumber'] == group_number)[0][subgroup_number]
        
        # Mask the data to select galaxies with a given GroupNumber and SubGroupNumber and particles inside a 30kpc sphere #
        galaxy_mask = np.where((self.stellar_data['GroupNumber'] == group_number) & (self.stellar_data['SubGroupNumber'] == subgroup_number) & (
            np.linalg.norm(np.subtract(self.stellar_data['Coordinates'], self.subhalo_data_tmp['CentreOfPotential'][halo_mask]),
                           axis=1) <= 30.0))  # kpc
        
        # Mask the temporary dictionary for each galaxy #
        stellar_data_tmp = {}
        for attribute in self.stellar_data.keys():
            stellar_data_tmp[attribute] = np.copy(self.stellar_data[attribute])[galaxy_mask]
        
        # Normalise the coordinates and velocities wrt the centre of potential of the subhalo #
        stellar_data_tmp['Coordinates'] = np.subtract(stellar_data_tmp['Coordinates'], self.subhalo_data_tmp['CentreOfPotential'][halo_mask])
        CoM_velocity = np.divide(np.sum(stellar_data_tmp['Mass'][:, np.newaxis] * stellar_data_tmp['Velocity'], axis=0),
                                 np.sum(stellar_data_tmp['Mass'], axis=0))  # km s-1
        stellar_data_tmp['Velocity'] = np.subtract(stellar_data_tmp['Velocity'], CoM_velocity)
        
        # Calculate the angular momentum for each particle and for the galaxy and the unit vector parallel to the galactic angular momentum vector #
        prc_angular_momentum = stellar_data_tmp['Mass'][:, np.newaxis] * np.cross(stellar_data_tmp['Coordinates'],
                                                                                  stellar_data_tmp['Velocity'])  # Msun kpc km s-1
        prc_unit_vector = np.divide(prc_angular_momentum, np.linalg.norm(prc_angular_momentum, axis=1)[:, np.newaxis])
        
        # Calculate kinematic diagnostics #
        kappa, disc_fraction, orbital, vrotsig, vrots, zaxis, momentum = MorphoKinematics.kinematics_diagnostics(stellar_data_tmp['Coordinates'],
                                                                                                                 stellar_data_tmp['Mass'],
                                                                                                                 stellar_data_tmp['Velocity'],
                                                                                                                 stellar_data_tmp[
                                                                                                                     'ParticleBindingEnergy'])
        
        # Calculate the ra and dec of the (unit vector of) angular momentum for each particle #
        ra = np.degrees(np.arctan2(prc_unit_vector[:, 1], prc_unit_vector[:, 0]))
        dec = np.degrees(np.arcsin(prc_unit_vector[:, 2]))
        
        # Create HEALPix map #
        nside = 2 ** 5  # Define the resolution of the grid (number of divisions along the side of a base-resolution pixel).
        hp = HEALPix(nside=nside)  # Initialise the HEALPix pixellisation class.
        indices = hp.lonlat_to_healpix(ra * u.deg, dec * u.deg)  # Create list of HEALPix indices from particles' ra and dec.
        density = np.bincount(indices, minlength=hp.npix)  # Count number of points in each HEALPix pixel.
        
        # Find location of density maximum and plot its positions and the ra and dec of the galactic angular momentum #
        index_densest = np.argmax(density)
        lon_densest = (hp.healpix_to_lonlat([index_densest])[0].value + np.pi) % (2 * np.pi) - np.pi
        lat_densest = (hp.healpix_to_lonlat([index_densest])[1].value + np.pi / 2) % (2 * np.pi) - np.pi / 2
        
        # Calculate disc mass fraction as the mass within 30 degrees from the densest pixel #
        glx_mass = np.sum(stellar_data_tmp['Mass'])
        angular_theta_from_densest = np.arccos(
            np.sin(lat_densest) * np.sin(np.arcsin(prc_unit_vector[:, 2])) + np.cos(lat_densest) * np.cos(np.arcsin(prc_unit_vector[:, 2])) * np.cos(
                lon_densest - np.arctan2(prc_unit_vector[:, 1], prc_unit_vector[:, 0])))  # In radians.
        disc_mask = np.where(angular_theta_from_densest < np.divide(np.pi, 6.0))
        disc_fraction_IT20 = np.divide(np.sum(stellar_data_tmp['Mass'][disc_mask]), np.sum(stellar_data_tmp['Mass']))
        
        return kappa, disc_fraction, disc_fraction_IT20, glx_mass
    
    
    @staticmethod
    def plot(kappas, disc_fractions, disc_fractions_IT20, glx_masses):
        """
        A method to plot a HEALPix histogram.
        :param kappas: from mask_galaxies
        :param disc_fractions: from mask_galaxies
        :param disc_fractions_IT20: from mask_galaxies
        :return: None
        """
        
        # Set the style of the plots #
        sns.set()
        sns.set_style('ticks')
        sns.set_context('notebook', font_scale=1.5)
        
        # Generate initial figure #
        plt.close()
        figure = plt.figure(figsize=(10, 7.5))
        plt.grid(True)
        # plt.ylim(0.0, 0.6)
        plt.ylabel(r'$\mathrm{f(B/T)_{\bigstar}}$')
        plt.xlabel(r'$\mathrm{(B/T)_{\bigstar}}$')
        
        mass_mask = np.where(glx_masses > 1e10)
        
        # Plots BBT19 bar's midpoints #
        BBT19 = np.genfromtxt('./Obs_Data/BBT19.csv', delimiter=',', names=['BT', 'f'])
        plt.scatter(BBT19['BT'], BBT19['f'], color='red', s=3, marker='_', zorder=2, label="$\mathrm{Bluck+19}$")
        
        # Weight each bin by the total number of values and make a histogram #
        weights = np.divide(np.ones_like(disc_fractions_IT20[mass_mask]), float(len(disc_fractions_IT20[mass_mask])))
        plt.hist(disc_fractions_IT20[mass_mask], weights=weights, edgecolor='black', bins=50)
        
        # Save the plot #
        plt.savefig(plots_path + 'DTT_PDF' + '-' + date + '.png', bbox_inches='tight')
        return None


if __name__ == '__main__':
    tag = '027_z000p101'
    simulation_path = '/cosma7/data/Eagle/ScienceRuns/Planck1/L0100N1504/PE/REFERENCE/data/'  # Path to EAGLE data.
    plots_path = '/cosma7/data/dp004/dc-irod1/EAGLE/python/plots/DTT_PDF/'  # Path to save plots.
    data_path = '/cosma7/data/dp004/dc-irod1/EAGLE/python/data/'  # Path to save/load data.
    if not os.path.exists(plots_path):
        os.makedirs(plots_path)
    x = DiscToTotalProbabilityDensityFunction(simulation_path, tag)