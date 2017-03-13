import os, time, ast
import json, geojson, geoio
import numpy as np
from shutil import copyfile, move
from net import VggNet
from gbdx_task_interface import GbdxTaskInterface

start = time.time()

class DeployCnnClassifier(GbdxTaskInterface):

    def __init__(self):
        '''
        Instantiate string and data inputs, organize data for training
        '''
        GbdxTaskInterface.__init__(self)

        # Get string inputs
        self.classes = self.get_input_string_port('classes', default=None)
        self.bit_depth = int(self.get_input_string_port('bit_depth', default='8'))
        self.min_side_dim = int(self.get_input_string_port('min_side_dim', default='0'))
        self.max_side_dim = ast.literal_eval(self.get_input_string_port('max_side_dim',
                                                                        default='None'))
        # Format classes
        if self.classes:
            self.classes = [clss.strip() for clss in self.classes.split(',')]

        # Get input dirs and files
        self.geoj_dir = self.get_input_data_port('geojson')
        self.model_inp = self.get_input_data_port('model')
        self.images_dir = self.get_input_data_port('images')

        # Move to images directory
        self.output_dir, self.imgs = self._format_working_directory()
        self.arch, self.weights, self.geoj = 'model.json', 'model.h5', 'geoj.geojson'


    def _format_working_directory(self):
        '''
        Make sure all input directories have proper files
        Move files to images folder to keep everything in one working directory
        '''

        # Identify files to move
        geoj_file = [f for f in os.listdir(self.geoj_dir) if f.endswith('.geojson')]
        arch_file = [f for f in os.listdir(self.model_inp) if f.endswith('.json')]
        weight_file = [f for f in os.listdir(self.model_inp) if f.endswith('.h5')]
        imgs = [img for img in os.listdir(self.images_dir) if img.endswith('.tif')]

        # Check for appropriate number of files in input dirs
        if len(geoj_file) != 1:
            raise Exception('Make sure there is exactly one geojson in image_dest s3 ' \
                            'bucket')
        if len(arch_file) != 1 or len(weight_file) != 1:
            raise Exception('Make sure there is exactly one json and h5 files in the ' \
                            'model directory')
        if len(imgs) == 0:
            raise Exception('No imagery found in input directory. Please make sure the' \
                            ' image directory has at least one tif image')

        # Get path to files
        geoj = os.path.join(self.geoj_dir, geoj_file[0])
        arch = os.path.join(self.model_inp, arch_file[0])
        weights = os.path.join(self.model_inp, weight_file[0])

        # Copy files to image dir
        copyfile(geoj, os.path.join(self.images_dir, 'geoj.geojson'))
        copyfile(arch, os.path.join(self.images_dir, 'model.json'))
        copyfile(weights, os.path.join(self.images_dir, 'model.h5'))

        # Make output directories
        output_dir = self.get_output_data_port('classified_geojson')
        os.makedirs(output_dir)

        # Move to new working dir, return output location and image list
        os.chdir(self.images_dir)
        return output_dir, imgs


    def invoke(self):
        '''
        Execute task
        '''

        # Load list of features
        with open(self.geoj) as f:
            info = geojson.load(f)['features']
            poly_ct = len(info)

        # Load trained model
        if self.classes:
            m = Net(classes=self.classes, model_name='model')
        else:
            m = Net(model_name='model')
        m.model.load_weights(self.weights)

        # Format input_shape and max_side_dim
        inp_shape = m.input_shape[-3:]

        if not self.max_side_dim:
            self.max_side_dim = inp_shape[-1]

        # Check all imgs have correct bands
        bands = inp_shape[0]
        for img in self.imgs:
            img_bands = geoio.GeoImage(img).shape[0]
            if bands != img_bands:
                raise Exception('Make sure the model was trained on an image with the ' \
                                'same number of bands as all input images.')

        # Filter shapefile
        gt.filter_polygon_size(self.geoj, output_file=self.geoj,
                               max_side_dim=self.max_side_dim,
                               min_side_dim=self.min_side_dim)

        # Numerical vs string classes
        out_name, num_classes = 'classified.geojson', True
        if self.classes:
            num_classes = False

        # Classify file
        m.classify_geojson(self.geoj, output_name=out_name, numerical_classes=num_classes,
                           max_side_dim=self.max_side_dim, min_side_dim=self.min_side_dim,
                           chips_in_mem=1000, bit_depth=self.bit_depth)

        # Write output
        move(out_name, self.output_dir)


if __name__ == '__main__':
    with DeployCnnClassifier() as task:
        task.invoke()
