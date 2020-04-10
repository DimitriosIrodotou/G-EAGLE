import re
import sys
import time
import h5py

import numpy as np
import astropy.units as u
import eagle_IO.eagle_IO.eagle_IO as E

from rotate_galaxies import RotateCoordinates
from morpho_kinematics import MorphoKinematics

date = time.strftime('%d_%m_%y_%H%M')  # Date
start_global_time = time.time()  # Start the global time.


class ReadAddAttributes:
    """
    For each galaxy: load its stellar_data_tmp dictionary and add the new attribute(s).
    """
    
    
    def __init__(self, simulation_path, tag):
        """
        A constructor method for the class.
        :param simulation_path: simulation directory
        :param tag: redshift directory
        """
        
        p = 1  # Counter.
        # Extract particle and subhalo attributes and convert them to astronomical units #
        self.stellar_data, self.gaseous_data, self.dark_matter_data, self.subhalo_data, self.FOF_data = self.read_attributes(simulation_path, tag)
        print('Read data for ' + re.split('Planck1/|/PE', simulation_path)[1] + ' in %.4s s' % (time.time() - start_global_time))
        print('–––––––––––––––––––––––––––––––––––––––––––––')
        
        self.subhalo_data_tmp = self.mask_haloes()  # Mask haloes: select haloes with masses within 30 kpc aperture higher than 1e9 Msun.
        
        job_number = int(sys.argv[1]) - 1
        # group_numbers = np.array_split(list(self.subhalo_data_tmp['GroupNumber']), 30)
        # subgroup_numbers = np.array_split(list(self.subhalo_data_tmp['SubGroupNumber']), 30)
        group_numbers = np.array_split(np.arange(1, 26), 5)
        subgroup_numbers = np.zeros(25, dtype=int)
        
        for group_number, subgroup_number in zip(group_numbers[job_number], subgroup_numbers):  # Loop over all masked haloes and sub-haloes.
            start_local_time = time.time()  # Start the local time.
            
            # Mask galaxies and normalise data #
            stellar_data_tmp, gaseous_data_tmp, dark_matter_data_tmp = self.mask_galaxies(group_number, subgroup_number)
            
            # Save data in numpy array #
            np.save(data_path + 'stellar_data_tmps/stellar_data_tmp_' + str(group_number) + '_' + str(subgroup_number), stellar_data_tmp)
            np.save(data_path + 'gaseous_data_tmps/gaseous_data_tmp_' + str(group_number) + '_' + str(subgroup_number), gaseous_data_tmp)
            np.save(data_path + 'dark_matter_data_tmps/dark_matter_data_tmp_' + str(group_number) + '_' + str(subgroup_number),
                    dark_matter_data_tmp)
            np.save(data_path + 'subhalo_data_tmps/subhalo_data_tmp_' + str(group_number) + '_' + str(subgroup_number), self.subhalo_data_tmp)
            np.save(data_path + 'FOF_data_tmps/FOF_data_tmp_' + str(group_number) + '_' + str(subgroup_number), self.FOF_data)
            
            print('Masked and saved data for halo ' + str(group_number) + ' in %.4s s' % (time.time() - start_local_time) + ' (' + str(
                round(100 * p / len(set(self.subhalo_data_tmp['GroupNumber'])), 1)) + '%)')
            print('–––––––––––––––––––––––––––––––––––––––––––––')
            p += 1
        
        print('Finished ReadAddAttributes for ' + re.split('Planck1/|/PE', simulation_path)[1] + ' in %.4s s' % (time.time() - start_global_time))
        print('–––––––––––––––––––––––––––––––––––––––––––––')
    
    
    def read_attributes(self, simulation_path, tag):
        """
        Extract particle and subhalo attributes and convert them to astronomical units.
        :param simulation_path: simulation directory
        :param tag: redshift folder
        :return: stellar_data, gaseous_data, dark_matter_data, subhalo_data, FOF_data
        """
        
        # Load particle data in h-free physical CGS units #
        stellar_data, gaseous_data, dark_matter_data = {}, {}, {}
        file_type = 'PARTDATA'
        particle_type = '4'
        for attribute in ['BirthDensity', 'Coordinates', 'GroupNumber', 'Mass', 'Metallicity', 'ParticleBindingEnergy', 'ParticleIDs',
                          'StellarFormationTime', 'SubGroupNumber', 'Velocity']:
            stellar_data[attribute] = E.read_array(file_type, simulation_path, tag, '/PartType' + particle_type + '/' + attribute, numThreads=8)
        
        particle_type = '0'
        for attribute in ['Coordinates', 'GroupNumber', 'Mass', 'ParticleIDs', 'StarFormationRate', 'SubGroupNumber', 'Velocity']:
            gaseous_data[attribute] = E.read_array(file_type, simulation_path, tag, '/PartType' + particle_type + '/' + attribute, numThreads=8)
        
        particle_type = '1'
        for attribute in ['Coordinates', 'GroupNumber', 'ParticleIDs', 'SubGroupNumber', 'Velocity']:
            dark_matter_data[attribute] = E.read_array(file_type, simulation_path, tag, '/PartType' + particle_type + '/' + attribute, numThreads=8)
        
        # Load subhalo data in h-free physical CGS units #
        subhalo_data = {}
        file_type = 'SUBFIND'
        for attribute in ['ApertureMeasurements/Mass/030kpc', 'CentreOfPotential', 'GroupNumber', 'IDMostBound', 'InitialMassWeightedStellarAge',
                          'SubGroupNumber']:
            subhalo_data[attribute] = E.read_array(file_type, simulation_path, tag, '/Subhalo/' + attribute, numThreads=8)
        
        # Load FOF data in h-free physical CGS units #
        FOF_data = {}
        file_type = 'SUBFIND'
        for attribute in ['Group_M_Crit200', 'FirstSubhaloID']:
            FOF_data[attribute] = E.read_array(file_type, simulation_path, tag, '/FOF/' + attribute, numThreads=8)
        
        # Convert attributes to astronomical units #
        stellar_data['Mass'] *= u.g.to(u.Msun)
        stellar_data['Velocity'] *= u.cm.to(u.km)  # per second.
        stellar_data['Coordinates'] *= u.cm.to(u.kpc)
        stellar_data['BirthDensity'] *= np.divide(u.g.to(u.Msun), u.cm.to(u.kpc) ** 3)
        
        gaseous_data['Mass'] *= u.g.to(u.Msun)
        gaseous_data['Velocity'] *= u.cm.to(u.km)  # per second.
        gaseous_data['Coordinates'] *= u.cm.to(u.kpc)
        
        dark_matter_data['Velocity'] *= u.cm.to(u.km)  # per second.
        dark_matter_data['Mass'] = self.dark_matter_mass(simulation_path, tag) * u.g.to(u.Msun)
        
        subhalo_data['CentreOfPotential'] *= u.cm.to(u.kpc)
        subhalo_data['ApertureMeasurements/Mass/030kpc'] *= u.g.to(u.Msun)
        
        FOF_data['Group_M_Crit200'] *= u.g.to(u.Msun)
        
        return stellar_data, gaseous_data, dark_matter_data, subhalo_data, FOF_data
    
    
    def mask_haloes(self):
        """
        Mask haloes: select haloes with masses within 30 kpc aperture higher than 1e9 Msun.
        :return: subhalo_data_tmp
        """
        
        # Mask the halo data #
        halo_mask = np.where(self.subhalo_data['ApertureMeasurements/Mass/030kpc'][:, 4] > 1e9)
        
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
        halo_mask, = np.where((self.subhalo_data_tmp['GroupNumber'] == group_number) & (self.subhalo_data_tmp['SubGroupNumber'] == subgroup_number))
        
        # Mask the data to select galaxies with a given GroupNumber and SubGroupNumber and particles inside a 30kpc sphere #
        stellar_mask = np.where((self.stellar_data['GroupNumber'] == group_number) & (self.stellar_data['SubGroupNumber'] == subgroup_number) & (
            np.linalg.norm(np.subtract(self.stellar_data['Coordinates'], self.subhalo_data_tmp['CentreOfPotential'][halo_mask]), axis=1) <= 30.0))
        
        gaseous_mask = np.where((self.gaseous_data['GroupNumber'] == group_number) & (self.gaseous_data['SubGroupNumber'] == subgroup_number) & (
            np.linalg.norm(np.subtract(self.gaseous_data['Coordinates'], self.subhalo_data_tmp['CentreOfPotential'][halo_mask]), axis=1) <= 30.0))
        
        dark_matter_mask = np.where(
            (self.dark_matter_data['GroupNumber'] == group_number) & (self.dark_matter_data['SubGroupNumber'] == subgroup_number) & (
                np.linalg.norm(np.subtract(self.dark_matter_data['Coordinates'], self.subhalo_data_tmp['CentreOfPotential'][halo_mask]),
                               axis=1) <= 30.0))
        
        # Mask the temporary dictionary for each galaxy #
        stellar_data_tmp, gaseous_data_tmp, dark_matter_data_tmp = {}, {}, {}
        for attribute in self.stellar_data.keys():
            stellar_data_tmp[attribute] = np.copy(self.stellar_data[attribute])[stellar_mask]
        for attribute in self.gaseous_data.keys():
            gaseous_data_tmp[attribute] = np.copy(self.gaseous_data[attribute])[gaseous_mask]
        for attribute in self.dark_matter_data.keys():
            dark_matter_data_tmp[attribute] = np.copy(self.dark_matter_data[attribute])[dark_matter_mask]
        
        # Normalise the coordinates and velocities wrt the centre of potential of the subhalo #
        for data in [stellar_data_tmp, gaseous_data_tmp, dark_matter_data_tmp]:
            data['Coordinates'] = np.subtract(data['Coordinates'], self.subhalo_data_tmp['CentreOfPotential'][halo_mask])
        
        # if self.subhalo_data_tmp['IDMostBound'][halo_mask] in stellar_data_tmp['ParticleIDs']:
        #     CoM_velocity = stellar_data_tmp['Velocity'][np.where(stellar_data_tmp['ParticleIDs'] == self.subhalo_data_tmp['IDMostBound'][
        #     halo_mask])]
        # elif self.subhalo_data_tmp['IDMostBound'][halo_mask] in dark_matter_data_tmp['ParticleIDs']:
        #     CoM_velocity = dark_matter_data_tmp['Velocity'][
        #         np.where(dark_matter_data_tmp['ParticleIDs'] == self.subhalo_data_tmp['IDMostBound'][halo_mask])]
        # elif self.subhalo_data_tmp['IDMostBound'][halo_mask] in gaseous_data_tmp['ParticleIDs']:
        #     CoM_velocity = gaseous_data_tmp['Velocity'][np.where(gaseous_data_tmp['ParticleIDs'] == self.subhalo_data_tmp['IDMostBound'][
        #     halo_mask])]
        
        CoM_velocity = np.divide(np.sum(stellar_data_tmp['Mass'][:, np.newaxis] * stellar_data_tmp['Velocity'], axis=0) + np.sum(
            gaseous_data_tmp['Mass'][:, np.newaxis] * gaseous_data_tmp['Velocity'], axis=0) + np.sum(
            dark_matter_data_tmp['Mass'][:, np.newaxis] * dark_matter_data_tmp['Velocity'], axis=0),
                                 np.sum(stellar_data_tmp['Mass'], axis=0) + np.sum(gaseous_data_tmp['Mass'], axis=0) + np.sum(
                                     dark_matter_data_tmp['Mass'], axis=0))  # km s-1
        for data in [stellar_data_tmp, gaseous_data_tmp, dark_matter_data_tmp]:
            data['Velocity'] = np.subtract(data['Velocity'], CoM_velocity)
        
        # Calculate the disc fraction and the rotational over dispersion velocity ratio #
        kappa_old, stellar_data_tmp['disc_fraction'], orbital, stellar_data_tmp[
            'rotational_over_dispersion'], vrots, zaxis, momentum = MorphoKinematics.kinematics_diagnostics(stellar_data_tmp['Coordinates'],
                                                                                                            stellar_data_tmp['Mass'],
                                                                                                            stellar_data_tmp['Velocity'],
                                                                                                            stellar_data_tmp['ParticleBindingEnergy'])
        
        # Calculate kappa #
        prc_spc_angular_momentum = np.cross(stellar_data_tmp['Coordinates'], stellar_data_tmp['Velocity'])  # kpc km s-1
        coordinates, velocity, prc_angular_momentum, glx_angular_momentum_old = RotateCoordinates.rotate_Jz(stellar_data_tmp)
        
        prc_cylindrical_distance = np.linalg.norm(np.dstack((coordinates[:, 0], coordinates[:, 1]))[0], axis=1)
        stellar_data_tmp['kappa'] = np.sum(
            0.5 * stellar_data_tmp['Mass'] * ((prc_spc_angular_momentum[:, 2] / prc_cylindrical_distance) ** 2)) / np.sum(
            0.5 * stellar_data_tmp['Mass'] * (np.linalg.norm(velocity, axis=1) ** 2))
        
        # Calculate the concentration index #
        stellar_data_tmp['c'] = np.divide(MorphoKinematics.r_ninety(stellar_data_tmp), MorphoKinematics.r_fifty(stellar_data_tmp))
        
        return stellar_data_tmp, gaseous_data_tmp, dark_matter_data_tmp
    
    
    @staticmethod
    def dark_matter_mass(simulation_path, tag):
        """
        Create a mass array for dark matter particles. As all dark matter particles share the same mass, there exists no PartType1/Mass dataset in
        the snapshot files.
        :return: particle_mass
        """
        # Read the required properties from the header and get conversion factors from gas particles #
        f = h5py.File(simulation_path + 'snapshot_' + tag + '/snap_027_z000p101.0.hdf5', 'r')
        a = f['Header'].attrs.get('Time')
        h = f['Header'].attrs.get('HubbleParam')
        n_particles = f['Header'].attrs.get('NumPart_Total')[1]
        dark_matter_mass = f['Header'].attrs.get('MassTable')[1]
        
        cgs = f['PartType0/Mass'].attrs.get('CGSConversionFactor')
        aexp = f['PartType0/Mass'].attrs.get('aexp-scale-exponent')
        hexp = f['PartType0/Mass'].attrs.get('h-scale-exponent')
        f.close()
        
        # Create an array of length equal to the number of dark matter particles and convert to h-free physical CGS units #
        particle_masses = np.ones(n_particles, dtype='f8') * dark_matter_mass
        particle_masses *= cgs * a ** aexp * h ** hexp
        
        return particle_masses


if __name__ == '__main__':
    tag = '027_z000p101'
    simulation_path = '/cosma7/data/Eagle/ScienceRuns/Planck1/L0100N1504/PE/REFERENCE/data/'  # Path to EAGLE data.
    data_path = '/cosma7/data/dp004/dc-irod1/EAGLE/python/data/'  # Path to save/load data.
    x = ReadAddAttributes(simulation_path, tag)
