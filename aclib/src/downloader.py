#!/usr/local/bin/python2.7
# encoding: utf-8
'''
downloader -- downloads components of aclib

@author:     Marius Lindauer
        
@copyright:  2013 AClib. All rights reserved.
        
@license:    GPL

@contact:    lindauer@informatik.uni-freiburg.de
'''

import os
import sys
import urllib
import tarfile
import traceback

class Downloader(object):
    '''
        downloads components of aclib 
    '''
    
    def __init__(self):
        '''
        constructor
        '''
        src_path = os.path.dirname(sys.argv[0])
        self._aclib_path, _ = os.path.split(src_path)
        if not self._aclib_path:
            self._aclib_path = "."
        
    def download_instances(self, instance_keys, repo, instance_dictionaries):
        '''
            download instances defined by instance_dict - config.json["instances"][key]
            requires user input to verify download size
            Args:
                instance_keys: list of name of instance set
                instance_dict: dictionaries of algo dictsshould contain "archive" with URL and "md5" for checksum
            Returns:
                True if download was successful
                False otherwise
        '''
        erronous_sets = []
        sum_size = 0
        for instance_key in instance_keys:
            instance_dict = instance_dictionaries[instance_key]
        
            if instance_dict.get("message"):
                sys.stderr.write(instance_dict.get("message")+"\n")
                sys.stderr.flush()
                return False
            
            archive = repo + "instances/" + instance_dict["download"]
    
            try:
                size_, _ = self.__get_size(archive)
                assert size_ > 0
            except AssertionError:
                sys.stderr.write("[ERROR] Unable to find %s\n" %(archive))
                erronous_sets.append(instance_key)
                continue
            except:
                traceback.print_exc()
                continue
                
            sum_size += size_
             
        print("Sum of all instance sets: %s" %(self.__convert_bytes(sum_size)))
        try:
            proceed = raw_input("Do you want to download all instance sets (y/n): ")
            if proceed != "y":
                return False
        except EOFError:
            pass

        ok_sets = set(instance_keys).difference(set(erronous_sets))
        
        for instance_key in ok_sets:
            instance_dict = instance_dictionaries[instance_key]
            problem_dir_ = os.path.join(self._aclib_path, "instances", instance_dict["problem_type"])
            data_dir = os.path.join(problem_dir_, "data")        
            download_file = os.path.join(data_dir, "instances.tar.gz")         
            # download
            try:
                if not os.path.isdir(data_dir):
                    os.makedirs(data_dir)
                
                archive = repo + "instances/" + instance_dict["download"]
                #(filename, _) = urllib.urlretrieve(archive, download_file)
                if not self.__download_file(archive, download_file): return False
                
                # extract archive
                print("Extract...")
                self.__extract_tar_gz(download_file, data_dir)
            finally:
                os.remove(download_file)
        return True
    
    def download_algorithms(self, algorithm_keys, repo, algorithm_dictionarys):
        '''
            download algorithm files
            Args:
                algorithm_key: key of algorithm (str)
                repro: url to repository
                files: list of files (including wrapper and binaries)
            Returns:
                True if successful
                False otherwise
        '''
        erronous_algos = []
        sum_size = 0        
        for algo_key in algorithm_keys:
            algorithm_dict = algorithm_dictionarys[algo_key]
        
        
            if algorithm_dict.get("message"):
                sys.stderr.write(algorithm_dict.get("message")+"\n")
                sys.stderr.flush()
                erronous_algos.append(algo_key)
                continue
        
        
            archive = algorithm_dict["download"]
            archive = repo + "target_algorithms/" + archive
            try: 
                size_ , _  = self.__get_size(archive)
                assert size_ > 0
            except AssertionError:
                sys.stderr.write("[ERROR] Unable to find %s\n" %(archive))
                erronous_algos.append(algo_key)
                continue
            except:
                traceback.print_exc()
                sys.stderr("[ERROR]: Unable to check size of %s\n" %(archive))
                erronous_algos.append(algo_key)
                continue
                
            sum_size += size_
        
        print("Size of all downloadable algorithms: %s" %(self.__convert_bytes(sum_size)))
        try:
            proceed = raw_input("Do you want to all these download algorithm files (y/n):")
            if proceed != "y":
                return False
        except EOFError:
            pass
        
        ok_algos = set(algorithm_keys).difference(set(erronous_algos))
        
        for algorithm_key in ok_algos:
            algorithm_dict = algorithm_dictionarys[algorithm_key]
        
            goal_path = self.__build_algorithm_folder_structure(algorithm_key, algorithm_dict["problem_type"])
            
            try:
                print("Download %s ..." %(algorithm_key))
                archive_name = os.path.basename(archive)
                (file_name, _) = urllib.urlretrieve(archive, os.path.join(goal_path, archive_name))
                self.__extract_tar_gz(file_name, goal_path)
            except:
                traceback.print_exc()
                sys.stderr.write("[ERROR]: Unable to download: %s\n" %(archive))
                continue
            finally:
                os.remove(file_name)
        
        return True
    
    def __build_algorithm_folder_structure(self, algorithm_key, problem_type_list):
        '''
            build the folder structure for a given algorithm
        '''
        if len(problem_type_list) > 1:
            goal_path = os.path.join(self._aclib_path, "target_algorithms", "multi_problem", algorithm_key)
        else:
            goal_path = os.path.join(self._aclib_path, "target_algorithms", problem_type_list[0], algorithm_key)
            
        try:
            if not os.path.isdir(goal_path):
                os.makedirs(goal_path)
        except:
            traceback.print_exc()
            
        if len(problem_type_list) > 1:
            for ptype in problem_type_list:
                type_path = os.path.join(self._aclib_path, "target_algorithms", ptype)
                try:
                    if not os.path.isdir(type_path):
                        os.makedirs(type_path)
                except: 
                    traceback.print_exc()
                try:
                    if not os.path.islink(os.path.join(self._aclib_path, type_path, algorithm_key)):
                        cwd = os.getcwd()
                        os.chdir(type_path)
                        #dest_ = os.path.join(type_path, algorithm_key)
                        goal_path_ = os.path.join("..","multi_problem",algorithm_key)
                        os.symlink(goal_path_, algorithm_key)
                        os.chdir(cwd)
                except:
                    traceback.print_exc()
        
        return goal_path
    
#===============================================================================
#     def download_scenario(self, scenario_key, url_, scenario_dict, problem_type, algorithm_problem_types):
#         '''
#             download all scenario files
#             Args:
#                 scenario_key: key of algorithm (str)
#                 url_: url to repository/website
#                 scenario_dict: list of files (including wrapper and binaries)
#                 problem_type: problem type of instance set
#                 algorithm_problem_types : problem types that can be handled by the algorithm
#             Returns:
#                 True if successful
#                 False otherwise
#         '''
#         files = ["scenarios/" + problem_type + "/" + scenario_key + "/scenario.txt",
#                  "target_algorithms/" + scenario_dict["pcs"],
#                  "instances/%s/sets/%s/training.txt" %(problem_type, scenario_dict["instances"]), # training.txt
#                  "instances/%s/sets/%s/test.txt" %(problem_type, scenario_dict["instances"]), # test.txt
#                  "instances/%s/sets/%s/README.md" %(problem_type, scenario_dict["instances"]) # README
#                  ]
#         
#         sum_size = 0
#         failed = False
#         for file_ in files:
#             file_ = url_ + file_
#             try:
#                 size_, _ = self.__get_size(file_)
#                 assert size_ > 0
#                 sum_size += float(size_)
#             except AssertionError:
#                 sys.stderr.write("[ERROR] Unable to find %s\n" %(file_))
#                 failed = True
#             except:
#                 traceback.print_exc()
#                 failed = True
#         if failed:
#             return False
#         
#         goal_path = os.path.join(self._aclib_path, "scenarios", problem_type, scenario_key)
#         converted_size = self.__convert_bytes(sum_size)
#         proceed = raw_input("Do you want to download scenarios files %s to %s (%s) (y/n): " %(scenario_key, goal_path, converted_size))
#         if proceed != "y":
#             return False
#         
#         # scenario file:
#         if not os.path.isdir(goal_path):
#             os.makedirs(goal_path)
#         source = url_ + "scenarios/" + problem_type + "/" + scenario_key + "/scenario.txt"
#         dest = os.path.join(goal_path, "scenario.txt")
#         if not self.__download_file(source, dest): return False
#         
#         # training and test file, README:
#         goal_path = os.path.join(self._aclib_path, "instances", problem_type, "sets", scenario_dict["instances"])
#         if not os.path.isdir(goal_path):
#             os.makedirs(goal_path)
#         source = url_ + "instances/%s/sets/%s/training.txt" %(problem_type, scenario_dict["instances"])
#         dest = os.path.join(goal_path, "training.txt")
#         if not self.__download_file(source, dest): return False
#         
#         source = url_ + "instances/%s/sets/%s/test.txt" %(problem_type, scenario_dict["instances"])
#         dest = os.path.join(goal_path, "test.txt")
#         if not self.__download_file(source, dest): return False
#         
#         source = url_ + "instances/%s/sets/%s/README.md" %(problem_type, scenario_dict["instances"])
#         dest = os.path.join(goal_path, "README.md")
#         if not self.__download_file(source, dest): return False
#         
#         source = url_ + "instances/%s/sets/%s/features.txt" % (problem_type, scenario_dict["instances"])
#         dest = os.path.join(goal_path, "features.txt")
#         if not self.__download_file(source, dest):
#             sys.stderr.write("[WARNING]: Could not find features.txt")
# 
#         # pcs file:
#         if len(algorithm_problem_types) > 1:
#             goal_path = os.path.join(self._aclib_path, "target_algorithms", "multi_problem", scenario_dict["algorithm"])
#         else:
#             goal_path = os.path.join(self._aclib_path, "target_algorithms", algorithm_problem_types[0], scenario_dict["algorithm"])
#         source = url_ + "target_algorithms/" + scenario_dict["pcs"]
#         basename = os.path.basename(scenario_dict["pcs"])
#         dest = os.path.join(goal_path, basename)
#         if not self.__download_file(source, dest): return False
#         
#         return True
#===============================================================================
    
    def __download_file(self, source, dest, verbose=True):
        '''
            download file from <source> to <dest>
            Returns:
                True if no exception occured
                False otherwise
        '''
        
        def __progress(count, blockSize, totalSize):
            '''
                report progress of download
            '''
            if totalSize > 0:
                percent_new = int(count*blockSize*100/totalSize)
                if percent_new < 100 and percent_new > __progress.percent_old:
                    sys.stdout.write(source + "...%d%%\r" % percent_new)
                    sys.stdout.flush()
                    __progress.percent_old = percent_new
        
        __progress.percent_old = -1
        try:
            print("Download...")
            sys.stdout.flush()
            (_, _) = urllib.urlretrieve(source, dest, reporthook=__progress)
            sys.stdout.write(source + "...%d%%\n" % 100)
        except:
            if verbose: traceback.print_exc()
            return False
        return True
    
    
    def __extract_tar_gz(self, file_, dir_):
        '''
            extract tar.gz archive into dir_
        '''
        try:
            cwd = os.getcwd()
            fp = tarfile.open(file_, "r:gz")
            os.chdir(dir_)
            try:
                fp.extractall()
            finally:
                fp.close()
        finally:
            os.chdir(cwd)
            
    def __get_size(self, url):
        ''' get size of file at <url> '''
        urlfile = urllib.urlopen(url)
        if urlfile.getcode() == 404:
            return -1, -1
        meta_file = urlfile.info()
        size_ = meta_file.getheaders("Content-Length")[0]
        converted_size = self.__convert_bytes(size_)
        print("Size of file %s is %s" %(url, converted_size))
        urlfile.close()
        return float(size_), converted_size
        
    def __convert_bytes(self, bytes_):
        '''
            http://snipperize.todayclose.com/snippet/py/Converting-Bytes-to-Tb/Gb/Mb/Kb--14257/
        '''
        bytes_ = float(bytes_)
        if bytes_ >= 1099511627776:
            terabytes = bytes_ / 1099511627776
            size = '%.2fT' % terabytes
        elif bytes_ >= 1073741824:
            gigabytes = bytes_ / 1073741824
            size = '%.2fG' % gigabytes
        elif bytes_ >= 1048576:
            megabytes = bytes_ / 1048576
            size = '%.2fM' % megabytes
        elif bytes_ >= 1024:
            kilobytes = bytes_ / 1024
            size = '%.2fK' % kilobytes
        else:
            size = '%.2fb' % bytes_
        return size
