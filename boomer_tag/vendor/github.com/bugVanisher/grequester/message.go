package grequester

import "github.com/golang/protobuf/proto"

// ProtoCodec ...
type ProtoCodec struct{}

// Marshal ...
func (s *ProtoCodec) Marshal(v interface{}) ([]byte, error) {
	return proto.Marshal(v.(proto.Message))
}

// Unmarshal ...
func (s *ProtoCodec) Unmarshal(data []byte, v interface{}) error {
	return proto.Unmarshal(data, v.(proto.Message))
}

// Name ...
func (s *ProtoCodec) Name() string {
	return "ProtoCodec"
}
