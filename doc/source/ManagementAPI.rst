Management API
==============

All notes to :ref:`kts46-cn-schedulerapi` are also applied to this API.


.. js:function:: addProject(projectName)

    Creates project with specified name.

    :param string projectName: Name of project to create.
    :returns: ``true`` if project has been succesfully added.
    :throws InvalidArgumentValue: project name is null, undefined or empty string.
    :throws InvalidArgumentType: project name is not a string.
    :throws ProjectExists: Project with this name already exists.


.. js:function:: deleteProject(projectName)

    Deletes specified project. This function doesn't throw an error if there is
    no project with specified name.

    :param string projectName: Name of project to delete.
    :throws InvalidArgumentValue: project name is null, undefined or empty string.
    :throws InvalidArgumentType: project name is not a string.
    :returns:
        ``true`` if project has been succesfully deleted or ``false`` if there
        is no such project.


.. js:function:: addJob(projectName, jobName, definition)

    Adds job to project.

    :param Object job: job to add.

    :param string projectName: Name of project to which to add job.
    :param string jobName: Name of job to add.
    :param Object definition: Definition of job.
    :returns: ``true`` if job has been succesfully added.
    :throws InvalidArgumentValue:
        project or job name is null, undefined or empty string or definition is
        null or undefined.
    :throws InvalidArgumentType: project or job name is not a string.
    :throws ProjectNotExists: There is no project with specified name.
    :throws JobAlreadyExists: There is already job with such name in this project.


.. js:function:: deleteJob(projectName, jobName)

    Deletes job from the project.

    :param string projectName: Name of jobs project.
    :param string jobName: Name of job to delete.
    :returns:
        ``true`` if job has been succesfully deleted or ``false`` if there is no
        such job.
    :throws InvalidArgumentValue:
        project or job name is null, undefined or empty string.
    :throws InvalidArgumentType: project or job name is not a string.
    :throws ProjectNotExists: There is no project with specified name.
