#! /usr/bin/env python
#
# This file is part of the Robot Learning Lab SDK
#
# Copyright (C) 2018 Wolfgang Wiedmeyer <wolfgang.wiedmeyer@kit.edu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import sys

import rospy
import actionlib

from rll_msgs.msg import JobStatus, JobEnvAction, JobEnvGoal


def job_result_codes_to_string(status):
    job_codes = {JobStatus.SUCCESS: "success", JobStatus.FAILURE: "failure",
                 JobStatus.INTERNAL_ERROR: "internal error"}
    return job_codes.get(status, "unknown")


def run_client(server_timeout, auth_secret):
    job_env = actionlib.SimpleActionClient('job_env', JobEnvAction)
    rospy.sleep(0.5)
    available = job_env.wait_for_server(
        rospy.Duration.from_sec(server_timeout))
    if not available:
        rospy.logerr("job env action server is not available")
        sys.exit(1)

    # TODO: move the project_runner into a module, so the code
    #       can be properly reused by tests
    job_env_goal = JobEnvGoal()
    job_env_goal.authentication_secret = auth_secret
    job_env_goal.client_ip_addr = "127.0.0.1"
    job_env.send_goal(job_env_goal)
    rospy.loginfo("started the project")
    job_env.wait_for_result()
    resp = job_env.get_result()

    if resp is None:
        rospy.logerr("job env action server did not return a response!")
        return False

    rospy.loginfo("executed project with status '%s'",
                  job_result_codes_to_string(resp.job.status))
    if resp.job_data:
        rospy.loginfo("extra job data:")
        for element in resp.job_data:
            rospy.loginfo("%s: %f", element.description, element.value)

    if resp.job.status == JobStatus.INTERNAL_ERROR:
        return False

    return True


# reset robot and environment
def idle(server_timeout, auth_secret):
    job_idle = actionlib.SimpleActionClient('job_idle', JobEnvAction)
    rospy.sleep(0.5)
    available = job_idle.wait_for_server(
        rospy.Duration.from_sec(server_timeout))
    if not available:
        rospy.logerr("job idle action server is not available")
        sys.exit(1)

    job_idle_goal = JobEnvGoal()
    job_idle_goal.authentication_secret = auth_secret
    job_idle.send_goal(job_idle_goal)
    rospy.loginfo("resetting environment back to start")
    job_idle.wait_for_result()
    resp = job_idle.get_result()
    rospy.loginfo("resetted environment with status '%s'",
                  job_result_codes_to_string(resp.job.status))
    if resp.job.status == JobStatus.INTERNAL_ERROR:
        rospy.logfatal("environment reset failed")
        sys.exit(1)


def run_project():
    server_timeout = rospy.get_param("~timeout", 5)
    auth_secret = rospy.get_param("~authentication_secret", "")
    only_idle = rospy.get_param("~only_idle")

    if only_idle:
        idle(server_timeout, auth_secret)
        sys.exit(0)

    success = run_client(server_timeout, auth_secret)
    if not success:
        rospy.logfatal("Internal error when running project")
        sys.exit(1)

    idle(server_timeout, auth_secret)


if __name__ == '__main__':
    rospy.init_node('project_runner')
    run_project()
