#!/bin/bash

cd ./components

ARGS="-m typelib -w -I /home/anthony/Programs/xulrunner_1.9.2_sdk/idl"
A="/host/Anthony/Projects/PyXUL/gui/components"
~/Programs/xulrunner_1.9.2_sdk/bin/xpidl $ARGS $A/nsIRoadNetworkModel.idl
~/Programs/xulrunner_1.9.2_sdk/bin/xpidl $ARGS $A/nsISimple.idl
~/Programs/xulrunner_1.9.2_sdk/bin/xpidl $ARGS $A/nsIRNModelParams.idl
~/Programs/xulrunner_1.9.2_sdk/bin/xpidl $ARGS $A/nsIProgressReportCallback.idl

cd ..
