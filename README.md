## A Tool for Distributing Codes.
SynCode is to distribute the codes from the source server to mulitple target servers.

## Installation

### Install the requirements.

#### The Source Server Side
1. Install `tmux` and `rsync`. `tmux` can show the status of SynCode. `rsync` is a fast and extraordinarily versatile file copying tool.

    ``` shell
    sudo apt update
    sudo apt install tmux
    sudo apt install rsync
    ```
    
2. Install `when-changed` which is used to monitor the changes of directory.
    
    ``` shell
    pip install https://github.com/joh/when-changed/archive/master.zip
    ```

3. Others

    ``` shell
    pip install -r requirements.txt
    ```

#### The Target Servers Sude

1. Install `rsync'.

``` shell
sudo apt update
sudo apt install rysnc
```

#### Usage

Consider there are two servers `A` and `B` which are source server and target server, respectively. 
    
1. First, we need to config the connection by using `ssh`. In particular, we add the following information to `~/.ssh/config`:

    ``` shell
    HOST server_B
    HOSTNAME $IP_OF_SERVER_B
    USER $USERNAME
    ```
    
2. Then, use `ssh server_B` to test whether server `A` can connect `B`. Use `ssh-copy-id` to remember password:
    
    ``` shell
    ssh-copy-id server_B
    ```
    
3. Now, all the preparations for SynCode have been done, we config the `source_path` in servet `A` and the `target_path` in server `B` in the `hosts.py` file. Here we give an example:
    
    ``` shell
    'sess_name': {
        'host_name': server_B',
        'source_path': 'source_path_in_server_A',
        'dest_path': 'target_path_in_server_B',
    },
    ```

4. Launch SynCode by following command:
    
    ``` shell
    python main.py
    ```
    
SynCode will new a new tmux session, where one window to show the running status of SynCode, others present the file records for distributing to other servers.
    


