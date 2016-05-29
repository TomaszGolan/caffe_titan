import caffe
import caffe.draw
from caffe.proto import caffe_pb2
from google.protobuf import text_format
import subprocess

net = caffe_pb2.NetParameter()
text_format.Merge(open("epsilon_127x50_xuv.prototxt.toplot").read(), net)

caffe.draw.draw_net_to_file(net, "caffe_epsilon.png", "TB")
