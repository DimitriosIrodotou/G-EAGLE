import os
import re
import time
import warnings
import argparse
import matplotlib
import access_database

matplotlib.use('Agg')

import numpy as np
import seaborn as sns
import matplotlib.cbook
import astropy.units as u
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import eagle_IO.eagle_IO.eagle_IO as E

from matplotlib import gridspec
from astropy_healpix import HEALPix
from rotate_galaxies import RotateCoordinates
from morpho_kinematics import MorphoKinematics

# Create a parser and add argument to read data #
parser = argparse.ArgumentParser(description='Create ra and dec plot.')
parser.add_argument('-r', action='store_true', help='Read data')
parser.add_argument('-l', action='store_true', help='Load data')
parser.add_argument('-rs', action='store_true', help='Read data and save to numpy arrays')
args = parser.parse_args()

date = time.strftime('%d_%m_%y_%H%M')  # Date
start_global_time = time.time()  # Start the global time.
warnings.filterwarnings('ignore', category=matplotlib.cbook.mplDeprecation)  # Ignore some plt warnings.


class RADec:
    """
    For each galaxy create: a HEALPix histogram from the angular momentum of particles - an angular distance plot - a surface density plot / mock
    image - a bar strength plot - a circularity distribution.
    a circularity plot.
    """
    
    
    def __init__(self, simulation_path, tag):
        """
        A constructor method for the class.
        :param simulation_path: simulation directory
        :param tag: redshift directory
        """
        
        p = 1  # Counter.
        # Initialise an array and a dictionary to store the data #
        glx_unit_vector, stellar_data_tmp = [], {}
        
        if not args.l:
            # Extract particle and subhalo attributes and convert them to astronomical units #
            self.stellar_data, self.subhalo_data = self.read_galaxies(simulation_path, tag)
            print('Read data for ' + re.split('Planck1/|/PE', simulation_path)[1] + ' in %.4s s' % (time.time() - start_global_time))
            print('–––––––––––––––––––––––––––––––––––––––––––––')
            
            self.subhalo_data_tmp = self.mask_haloes()  # Mask haloes: select haloes with masses within 30 kpc aperture higher than 1e8 Msun.
        
        # for group_number in np.sort(list(set(self.subhalo_data_tmp['GroupNumber']))):  # Loop over all masked haloes.
        for group_number in range(25, 26):  # Loop over all masked haloes.
            for subgroup_number in range(0, 1):  # Get centrals only.
                if args.rs:  # Read and save data.
                    start_local_time = time.time()  # Start the local time.
                    
                    stellar_data_tmp, glx_unit_vector = self.mask_galaxies(group_number, subgroup_number)  # Mask galaxies and normalise data.
                    
                    # Save data in numpy arrays #
                    np.save(data_path + 'glx_unit_vectors/' + 'glx_unit_vector_' + str(group_number) + '_' + str(subgroup_number), glx_unit_vector)
                    np.save(data_path + 'stellar_data_tmps/' + 'stellar_data_tmp_' + str(group_number) + '_' + str(subgroup_number), stellar_data_tmp)
                    print('Masked and saved data for halo ' + str(group_number) + ' in %.4s s' % (time.time() - start_local_time) + ' (' + str(
                        round(100 * p / len(set(self.subhalo_data_tmp['GroupNumber'])), 1)) + '%)')
                    print('–––––––––––––––––––––––––––––––––––––––––––––')
                    p += 1
                
                elif args.r:  # Read data.
                    start_local_time = time.time()  # Start the local time.
                    
                    stellar_data_tmp, glx_unit_vector = self.mask_galaxies(group_number, subgroup_number)  # Mask galaxies and normalise data.
                    print('Masked data for halo ' + str(group_number) + ' in %.4s s' % (time.time() - start_local_time) + ' (' + str(
                        round(100 * p / len(set(self.subhalo_data_tmp['GroupNumber'])), 1)) + '%)')
                    print('–––––––––––––––––––––––––––––––––––––––––––––')
                    p += 1
                
                elif args.l:  # Load data.
                    start_local_time = time.time()  # Start the local time.
                    
                    # Load data from numpy arrays #
                    glx_unit_vector = np.load(
                        data_path + 'glx_unit_vectors/' + 'glx_unit_vector_' + str(group_number) + '_' + str(subgroup_number) + '.npy')
                    stellar_data_tmp = np.load(
                        data_path + 'stellar_data_tmps/' + 'stellar_data_tmp_' + str(group_number) + '_' + str(subgroup_number) + '.npy',
                        allow_pickle=True)
                    stellar_data_tmp = stellar_data_tmp.item()
                    print('Loaded data for halo ' + str(group_number) + ' in %.4s s' % (time.time() - start_local_time))
                    print('–––––––––––––––––––––––––––––––––––––––––––––')
                
                # Plot the data #
                start_local_time = time.time()  # Start the local time.
                
                self.plot(stellar_data_tmp, glx_unit_vector, group_number, subgroup_number)
                print('Plotted data for halo ' + str(group_number) + ' in %.4s s' % (time.time() - start_local_time))
                print('–––––––––––––––––––––––––––––––––––––––––––––')
        
        print('Finished RADec for ' + re.split('Planck1/|/PE', simulation_path)[1] + ' in %.4s s' % (time.time() - start_global_time))
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
        Mask haloes: select haloes with masses within 30 kpc aperture higher than 1e8 Msun.
        :return: subhalo_data_tmp
        """
        
        # Mask the halo data #
        halo_mask = np.where(self.subhalo_data['ApertureMeasurements/Mass/030kpc'][:, 4] > 1e8)
        
        # Mask the temporary dictionary for each galaxy #
        subhalo_data_tmp = {}
        for attribute in self.subhalo_data.keys():
            subhalo_data_tmp[attribute] = np.copy(self.subhalo_data[attribute])[halo_mask]
        
        return subhalo_data_tmp
    
    
    def mask_galaxies(self, group_number, subgroup_number):
        """
        Mask galaxies and normalise data.
        :param group_number: from list(set(self.subhalo_data_tmp['GroupNumber']))
        :param subgroup_number: from list(set(self.subhalo_data_tmp['SubGroupNumber']))
        :return: stellar_data_tmp, glx_unit_vector
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
        glx_angular_momentum = np.sum(prc_angular_momentum, axis=0)  # Msun kpc km s-1
        glx_unit_vector = np.divide(glx_angular_momentum, np.linalg.norm(glx_angular_momentum))
        
        return stellar_data_tmp, glx_unit_vector
    
    
    @staticmethod
    def plot(stellar_data_tmp, glx_unit_vector, group_number, subgroup_number):
        """
        Plot a HEALPix histogram from the angular momentum of particles - an angular distance plot - a surface density plot / mock image - a bar
        strength plot - a circularity distribution.
        :param stellar_data_tmp: from mask_galaxies
        :param glx_unit_vector: from mask_galaxies
        :param group_number: from list(set(self.subhalo_data_tmp['GroupNumber']))
        :param subgroup_number: from list(set(self.subhalo_data_tmp['SubGroupNumber']))
        :return: None
        """
        
        # Set the style of the plots #
        sns.set()
        sns.set_style('ticks')
        sns.set_context('notebook', font_scale=1.6)
        
        # Generate the figure and define its parameters #
        plt.close()
        plt.figure(0, figsize=(20, 22.5))
        
        gs = gridspec.GridSpec(3, 2)
        ax00 = plt.subplot(gs[0, 0], projection='mollweide')
        ax01 = plt.subplot(gs[0, 1])
        ax10 = plt.subplot(gs[1, 0])
        ax11 = plt.subplot(gs[1, 1])
        ax20 = plt.subplot(gs[2, 0])
        ax21 = plt.subplot(gs[2, 1])
        
        for a in [ax10, ax11, ax20, ax21]:
            a.grid(True)
        
        for a in [ax10, ax11]:
            a.set_xlim(-10, 190)
            a.set_xticks(np.arange(0, 181, 20))
        
        ax01.axis('off')
        
        ax20.set_ylim(-0.2, 1.2)
        ax20.set_xlim(0.0, 10.0)
        
        ax00.set_xlabel('RA ($\degree$)')
        ax00.set_ylabel('Dec ($\degree$)')
        ax10.set_ylabel('Particles per grid cell')
        ax10.set_xlabel('Angular distance from X ($\degree$)')
        ax11.set_ylabel('Particles per grid cell')
        ax11.set_xlabel('Angular distance from densest grid cell ($\degree$)')
        ax20.set_xlabel('R [kpc]')
        ax20.set_ylabel('$\mathrm{A_{2}}$')
        ax21.set_xlabel('$\mathrm{\epsilon}$')
        ax21.set_ylabel('$\mathrm{f(\epsilon)}$')
        
        # Set manually the values of the ra axis #
        ax00.annotate(r'0', xy=(0 - np.pi / 40, - np.pi / 65), xycoords='data', size=18)
        ax00.annotate(r'30', xy=(np.pi / 6 - np.pi / 25, - np.pi / 65), xycoords='data', size=18)
        ax00.annotate(r'-30', xy=(-np.pi / 6 - np.pi / 15, - np.pi / 65), xycoords='data', size=18)
        ax00.annotate(r'60', xy=(np.pi / 3 - np.pi / 25, - np.pi / 65), xycoords='data', size=18)
        ax00.annotate(r'-60', xy=(-np.pi / 3 - np.pi / 15, - np.pi / 65), xycoords='data', size=18)
        ax00.annotate(r'90', xy=(np.pi / 2 - np.pi / 25, - np.pi / 65), xycoords='data', size=18)
        ax00.annotate(r'-90', xy=(-np.pi / 2 - np.pi / 15, -np.pi / 65), xycoords='data', size=18)
        ax00.annotate(r'120', xy=(2 * np.pi / 3 - np.pi / 15, -np.pi / 65), xycoords='data', size=18)
        ax00.annotate(r'-120', xy=(-2 * np.pi / 3 - np.pi / 10, -np.pi / 65), xycoords='data', size=18)
        ax00.annotate(r'150', xy=(2.5 * np.pi / 3 - np.pi / 15, -np.pi / 65), xycoords='data', size=18)
        ax00.annotate(r'-150', xy=(-2.5 * np.pi / 3 - np.pi / 10, -np.pi / 65), xycoords='data', size=18)
        
        # Rotate coordinates and velocities of stellar particles so the galactic angular momentum points along the x axis #
        stellar_data_tmp['Coordinates'], stellar_data_tmp['Velocity'], prc_unit_vector, glx_unit_vector = RotateCoordinates.rotate_X(stellar_data_tmp,
                                                                                                                                     glx_unit_vector)
        
        # Calculate the ra and dec of the (unit vector of) angular momentum for each particle #
        ra = np.degrees(np.arctan2(prc_unit_vector[:, 1], prc_unit_vector[:, 0]))
        dec = np.degrees(np.arcsin(prc_unit_vector[:, 2]))
        
        # Plot a HEALPix histogram #
        nside = 2 ** 5  # Define the resolution of the grid (number of divisions along the side of a base-resolution pixel).
        hp = HEALPix(nside=nside)  # Initialise the HEALPix pixellisation class.
        indices = hp.lonlat_to_healpix(ra * u.deg, dec * u.deg)  # Create list of HEALPix indices from particles' ra and dec.
        density = np.bincount(indices, minlength=hp.npix)  # Count number of points in each HEALPix pixel.
        
        # Find location of density maximum and plot its positions and the ra and dec of the galactic angular momentum #
        index_densest = np.argmax(density)
        lon_densest = (hp.healpix_to_lonlat([index_densest])[0].value + np.pi) % (2 * np.pi) - np.pi
        lat_densest = (hp.healpix_to_lonlat([index_densest])[1].value + np.pi / 2) % (2 * np.pi) - np.pi / 2
        ax00.annotate(r'Density maximum', xy=(lon_densest, lat_densest), xycoords='data', xytext=(0.78, 1.00), textcoords='axes fraction',
                      arrowprops=dict(arrowstyle='-', color='black', connectionstyle='arc3,rad=0'))  # Position of the densest pixel.
        ax00.scatter(np.arctan2(glx_unit_vector[1], glx_unit_vector[0]), np.arcsin(glx_unit_vector[2]), s=300, color='black', marker='X',
                     zorder=5)  # Position of the galactic angular momentum.
        
        # Sample a 360x180 grid in ra/dec #
        ra = np.linspace(-180.0, 180.0, num=360) * u.deg
        dec = np.linspace(-90.0, 90.0, num=180) * u.deg
        ra_grid, dec_grid = np.meshgrid(ra, dec)
        
        # Find density at each coordinate position #
        coordinate_index = hp.lonlat_to_healpix(ra_grid, dec_grid)
        density_map = density[coordinate_index]
        
        # Display data on a 2D regular raster and create a pseudo-color plot #
        im = ax00.imshow(density_map, cmap='nipy_spectral_r', aspect='auto', norm=matplotlib.colors.LogNorm(vmin=1))
        cbar = plt.colorbar(im, ax=ax00, orientation='horizontal')
        cbar.set_label('$\mathrm{Particles\; per\; grid\; cell}$')
        ax00.pcolormesh(np.radians(ra), np.radians(dec), density_map, cmap='nipy_spectral_r')
        
        # Calculate disc mass fraction as the mass within 30 degrees from the densest pixel #
        angular_theta_from_densest = np.arccos(
            np.sin(lat_densest) * np.sin(np.arcsin(prc_unit_vector[:, 2])) + np.cos(lat_densest) * np.cos(np.arcsin(prc_unit_vector[:, 2])) * np.cos(
                lon_densest - np.arctan2(prc_unit_vector[:, 1], prc_unit_vector[:, 0])))  # In radians.
        disc_mask = np.where(angular_theta_from_densest < np.divide(np.pi, 6.0))
        disc_fraction_IT20 = np.divide(np.sum(stellar_data_tmp['Mass'][disc_mask]), np.sum(stellar_data_tmp['Mass']))
        
        # Plot the 2D surface density projection #
        galaxy_id = access_database.download_image(group_number, subgroup_number)
        img2 = mpimg.imread(data_path + 'images/galface_' + galaxy_id)
        ax01.imshow(img2)
        
        # Calculate and plot the angular distance (spherical law of cosines) between the densest and all the other grid cells #
        angular_theta_from_densest = np.arccos(
            np.sin(lat_densest) * np.sin(np.radians(dec_grid.value)) + np.cos(lat_densest) * np.cos(np.radians(dec_grid.value)) * np.cos(
                lon_densest - np.radians(ra_grid.value)))  # In radians.
        
        ax11.scatter(angular_theta_from_densest[density_map.nonzero()] * np.divide(180.0, np.pi), density_map[density_map.nonzero()], c='black',
                     s=10)  # In degrees.
        ax11.axvline(x=30, c='blue', lw=3, linestyle='dashed', label='D/T= %.3f ' % disc_fraction_IT20)  # Vertical line at 30 degrees.
        ax11.axvspan(0, 30, facecolor='0.2', alpha=0.5)  # Draw a vertical span.
        ax11.legend(loc='upper center', fontsize=16, frameon=False, scatterpoints=3)
        
        # Calculate the kinematic diagnostics #
        kappa, discfrac, orbital, vrotsig, vrots, zaxis, momentum = MorphoKinematics.kinematics_diagnostics(
            np.fliplr(stellar_data_tmp['Coordinates']), stellar_data_tmp['Mass'], np.fliplr(stellar_data_tmp['Velocity']),
            stellar_data_tmp['ParticleBindingEnergy'])
        
        # Calculate and plot the distribution of orbital circularity #
        j, = np.where((orbital < 0.0))
        k, = np.where((orbital > 0.7) & (orbital < 1.7))
        l, = np.where((orbital > -1.7) & (orbital < 1.7))
        disc_fraction_00 = 1 - 2 * np.sum(stellar_data_tmp['Mass'][j]) / np.sum(stellar_data_tmp['Mass'][l])
        disc_fraction_07 = np.sum(stellar_data_tmp['Mass'][k]) / np.sum(stellar_data_tmp['Mass'][l])
        
        ydata, edges = np.histogram(orbital, bins=100, range=[-1.7, 1.7], weights=stellar_data_tmp['Mass'] / np.sum(stellar_data_tmp['Mass']))
        ydata /= edges[1:] - edges[:-1]
        ax21.plot(0.5 * (edges[1:] + edges[:-1]), ydata, label='D/T = %.3f' % disc_fraction_07)
        ax21.legend(loc='upper left', fontsize=16, frameon=False, scatterpoints=3)
        
        # Calculate and plot the angular distance between the (unit vector of) the galactic angular momentum and all the other grid cells #
        position_of_X = np.vstack([np.arctan2(glx_unit_vector[1], glx_unit_vector[0]), np.arcsin(glx_unit_vector[2])]).T
        
        angular_theta_from_X = np.arccos(np.sin(position_of_X[0, 1]) * np.sin(np.radians(dec_grid.value)) + np.cos(position_of_X[0, 1]) * np.cos(
            np.radians(dec_grid.value)) * np.cos(position_of_X[0, 0] - np.radians(ra_grid.value)))  # In radians.
        ax10.scatter(angular_theta_from_X[density_map.nonzero()] * np.divide(180.0, np.pi), density_map[density_map.nonzero()], c='black',
                     s=10)  # In degrees.
        ax10.axvline(x=90, c='red', lw=3, linestyle='dashed', label='D/T= %.3f ' % disc_fraction_00)  # Vertical line at 30 degrees.
        ax10.axvspan(90, 180, facecolor='0.2', alpha=0.5)  # Draw a vertical span.
        ax10.legend(loc='upper center', fontsize=16, frameon=False, scatterpoints=3)
        
        # Calculate and plot the bar strength from Fourier modes of surface density as a function of radius plot #
        nbins = 40  # Number of radial bins.
        r = np.sqrt(stellar_data_tmp['Coordinates'][:, 2] ** 2 + stellar_data_tmp['Coordinates'][:, 1] ** 2)  # Radius of each particle.
        
        # Initialise Fourier components #
        r_m = np.zeros(nbins)
        beta_2 = np.zeros(nbins)
        alpha_0 = np.zeros(nbins)
        alpha_2 = np.zeros(nbins)
        
        # Split up galaxy in radius bins and calculate Fourier components #
        for i in range(0, nbins):
            r_s = float(i) * 0.25
            r_b = float(i) * 0.25 + 0.25
            r_m[i] = float(i) * 0.25 + 0.125
            xfit = stellar_data_tmp['Coordinates'][:, 2][(r < r_b) & (r > r_s)]
            yfit = stellar_data_tmp['Coordinates'][:, 1][(r < r_b) & (r > r_s)]
            for k in range(0, len(xfit)):
                th_i = np.arctan2(yfit[k], xfit[k])
                alpha_0[i] = alpha_0[i] + 1
                alpha_2[i] = alpha_2[i] + np.cos(2 * th_i)
                beta_2[i] = beta_2[i] + np.sin(2 * th_i)
        
        a2 = np.divide(np.sqrt(alpha_2[:] ** 2 + beta_2[:] ** 2), alpha_0[:])
        
        ax20.plot(r_m, a2, label='Bar strength: %.2f' % max(a2))
        ax20.legend(loc='upper left', fontsize=16, frameon=False, scatterpoints=3)
        
        # Save the plot #
        plt.savefig(plots_path + str(group_number) + str(subgroup_number) + '-' + 'RD' + '-' + date + '.png', bbox_inches='tight')
        return None


if __name__ == '__main__':
    tag = '027_z000p101'
    simulation_path = '/cosma7/data/Eagle/ScienceRuns/Planck1/L0100N1504/PE/REFERENCE/data/'  # Path to EAGLE data.
    plots_path = '/cosma7/data/dp004/dc-irod1/EAGLE/python/plots/RD/'  # Path to save plots.
    data_path = '/cosma7/data/dp004/dc-irod1/EAGLE/python/data/'  # Path to save/load data.
    if not os.path.exists(plots_path):
        os.makedirs(plots_path)
    x = RADec(simulation_path, tag)
