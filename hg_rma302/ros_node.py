"""ROS adapter; serial/power/IMU ownership stays in the existing main loop."""

from dataclasses import replace
import math
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import Joy

from .cli import run
from .config import load_config
from .control import InputState
from .joy_input import JoyMapping, decode_joy


class RosJoyInput:
    requires_event_updates = True

    def __init__(self, node, mapping, topic, timeout_s):
        self.node = node
        self.mapping = mapping
        self.timeout_s = timeout_s
        self.source_description = f'ROS {topic}; joy_linux XInput; LB deadman'
        self.state = InputState(connected=False)
        self.frames = []
        self.subscription = node.create_subscription(
            Joy, topic, self.receive,
            QoSProfile(history=HistoryPolicy.KEEP_LAST, depth=64,
                       reliability=ReliabilityPolicy.BEST_EFFORT,
                       durability=DurabilityPolicy.VOLATILE))

    def receive(self, message):
        stamp_ns = message.header.stamp.sec * 1_000_000_000 + message.header.stamp.nanosec
        age = (self.node.get_clock().now().nanoseconds - stamp_ns) / 1e9
        self.state = decode_joy(
            message.axes, message.buttons, received_at=time.monotonic(),
            stamp_age_s=age, timeout_s=self.timeout_s, mapping=self.mapping)
        self.frames.append(self.state)

    def read(self):
        if not rclpy.ok(context=self.node.context):
            raise RuntimeError('ROS context shut down')
        # Bound callback work; preserve every delivered B/neutral edge.
        for _ in range(64):
            count = len(self.frames)
            rclpy.spin_once(self.node, timeout_sec=0)
            if len(self.frames) == count:
                break
        else:
            raise RuntimeError('ROS joy callback queue overflow')
        frames, self.frames = self.frames, []
        return frames

    def close(self):
        self.node.destroy_subscription(self.subscription)


def main(args=None):
    # The motor loop owns SIGINT/SIGTERM and performs its stop/SSR cleanup first.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = Node('hg_rma302_driver')
    try:
        def parameter(name, default):
            return (node.get_parameter(name) if node.has_parameter(name)
                    else node.declare_parameter(name, default)).value

        if parameter('use_sim_time', False):
            raise ValueError('Physical joy driving requires use_sim_time=false')
        path = parameter('config_file', '')
        if not path:
            raise ValueError('Set config_file to the robot JSON (absolute path)')
        config = load_config(path)
        mode = parameter('control_mode', 'joystick')
        config = replace(config, drive=replace(config.drive, control_mode=mode))
        live = parameter('live', False)
        topic = parameter('joy_topic', '/joy')
        mapping = JoyMapping(**{
            name: parameter('mapping.' + name, default)
            for name, default in vars(JoyMapping()).items()})
        log_path = parameter('log_path', '')
        seconds = parameter('seconds', 0.0)
        if (not isinstance(live, bool) or not isinstance(seconds, (int, float))
                or not math.isfinite(seconds) or seconds < 0):
            raise ValueError('live must be boolean; seconds must be nonnegative')
        node.get_logger().info(f'{"LIVE" if live else "DRY RUN"}: {topic}; LB deadman; {mode}')
        run(config, live=live, seconds=seconds or None, log_path=log_path or None,
            gamepad_factory=lambda _path, *, event_timeout_s: RosJoyInput(
                node, mapping, topic, event_timeout_s))
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
