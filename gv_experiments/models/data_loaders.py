import torch
from torch.utils.data import Dataset
import numpy as np
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split


class ChEMBL_Dataset(Dataset):
    def __init__(self, chembl_fp_df=None):
        self.molecule_chembl_id = chembl_fp_df["molecule_chembl_id"].values
        self.fingerprints = chembl_fp_df.iloc[:, 1].values
        # self.drugs_tensor = torch.tensor(
        #     [
        #         [int(v) for v in list(row)]
        #         for row in fingerprints
        #     ]
        # ).float()

    def __len__(self): 
        return len(self.molecule_chembl_id)

    def __getitem__(self, idx):
        chembl_mol_id = self.molecule_chembl_id[idx]
        fingerprint = self.fingerprints[idx]
        fingerprint =  torch.tensor([int(v) for v in list(fingerprint)]).float()
        return fingerprint, chembl_mol_id



class DrugResistanceDataset(Dataset):
    def __init__(
        self,
        long_table_df,
        spectra_matrix,
        drugs_df, 
        species_list
    ):
        """
        Dataset class to retrieve combinations of species-samples-drugs-drug resistance quadruplets

        :long_table: DataFrame from processed csv file with the quadruplets for each hospital
        :spectra_matrix: matrix of 6000-dimensional MALDI-TOF spectra
        :drugs_df: DataFrame of embeddings derived from the ChEMBL VAE from morgan fingerprints
        """
        self.long_table = long_table_df
        self.spectra_tensor = torch.tensor(spectra_matrix).float()

        sorted_species = sorted(long_table_df["species"].unique())
        self.idx2species = {i: s for i, s in enumerate(sorted_species)}
        self.species2idx = {s: i for i, s in self.idx2species.items()}

        # sorted_samples = sorted(long_table_df["sample_id"].unique())
        self.idx2sample = {i: smp for i, smp in enumerate(species_list)}
        self.sample2idx = {smp: i for i, smp in self.idx2sample.items()}

        self.idx2drug = {i: d for i,
                         d in enumerate(drugs_df.index)}
        self.drug2idx = {d: i for i, d in self.idx2drug.items()}

    def __len__(self):
        return len(self.long_table)

    def __getitem__(self, idx):
        species, sample_id, drug_name, response, dataset = self.long_table.iloc[idx]

        fprint_tensor = self.drugs_tensor[self.drug2idx[drug_name]]
        response = torch.tensor(response).float()

        spectrum = self.spectra_tensor[self.sample2idx[sample_id], :]

        species_idx = torch.LongTensor([self.species2idx[species]])
        return species_idx, spectrum, fprint_tensor, response, dataset



class DrugResistanceDataset_VAEEmbeddings(DrugResistanceDataset):
    def __init__(
        self,
        long_table_df,
        spectra_matrix,
        drugs_embeddings, 
        species_list
    ):
        super().__init__(long_table_df, spectra_matrix, drugs_embeddings, species_list)
        self.drugs_tensor = torch.from_numpy(drugs_embeddings.values/np.sum(drugs_embeddings.values)).float()



class DrugResistanceDataset_Fingerprints(DrugResistanceDataset):
    def __init__(
        self,
        long_table_df,
        spectra_matrix,
        drugs_fingerprints, 
        species_list,
        fingerprint_class="MACCS"
    ):
        super().__init__(long_table_df, spectra_matrix, drugs_fingerprints, species_list)
        
        self.drugs_tensor = torch.tensor(
            [
                [int(v) for v in list(row[fingerprint_class + "_fp"])]
                for i, row in drugs_fingerprints.iterrows()
            ]
        ).float()

class SampleEmbDataset(Dataset):
    def __init__(self, long_table, spectra_matrix):
        self.spectra_tensor = torch.tensor(spectra_matrix).float()

        sorted_species = sorted(long_table["species"].unique())
        self.idx2species = {i: s for i, s in enumerate(sorted_species)}
        self.species2idx = {s: i for i, s in self.idx2species.items()}

        sorted_samples = sorted(long_table["sample_id"].unique())
        self.idx2sample = {i: smp for i, smp in enumerate(sorted_samples)}
        self.sample2idx = {smp: i for i, smp in self.idx2sample.items()}

        # Filter long table
        long_table = long_table.drop(["drug", "response"], axis=1)
        long_table = long_table.drop_duplicates()
        self.long_table = long_table

    def __len__(self):
        return len(self.long_table)

    def __getitem__(self, idx):
        species, sample_id = self.long_table.iloc[idx]
        spectrum = self.spectra_tensor[self.sample2idx[sample_id], :]
        species_idx = torch.LongTensor([self.species2idx[species]])
        return species_idx, spectrum