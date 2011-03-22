exports.serverStatus = function(projectStorage, args, onFinish, onError){
    projectStorage.getStatus(onFinish, onError);
};

exports.getJobStatistics = function(projectStorage, args, onFinish, onError){
    projectStorage.getJobStatistics(args.project, args.job, onFinish, onError);
};
