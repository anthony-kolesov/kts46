exports.serverStatus = function(projectStorage, args, onFinish, onError){
    projectStorage.getStatus(onFinish, onError);
};

exports.getJobStatistics = function(projectStorage, args, onFinish, onError){
    projectStorage.getJobStatistics(args.project, args.job, onFinish, onError);
};

exports.getModelDefinition = function(projectStorage, args, onFinish, onError){
    projectStorage.getModelDefinition(args.project, args.job, onFinish, onError);
};
