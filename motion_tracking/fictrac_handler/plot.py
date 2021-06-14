

def angle_diff(angle1, angle2):
    diff = angle2 - angle1
    while diff < np.deg2rad(-180.0):
        diff += np.deg2rad(360.0)
    while diff > np.deg2rad(180):
        diff -= np.deg2rad(360.0)
    return diff

def plot_task_fictrac(remote_endpoint_url,
                      fictrac_state_fields=['speed', 'direction', 'del_rot_cam_vec', 'del_rot_error'],
                      num_history=200):
    """
    A coroutine for plotting fast, realtime as per: https://gist.github.com/pklaus/62e649be55681961f6c4. This is used
    for plotting streaming data coming from FicTrac.

    :param disp_queue: The message queue from which data is sent for plotting.
    :return: None
    """

    # Open or create the shared memory region for accessing FicTrac's state
    shmem = mmap.mmap(-1, ctypes.sizeof(fictrac.FicTracState), "FicTracStateSHMEM")

    warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)
    plt.ion()

    fig = plt.figure()
    fig.canvas.set_window_title('traces: fictrac_handler')

    # Number of fields to display
    num_channels = len(fictrac_state_fields)

    # Axes limits for each field
    field_ax_limits = {'speed': (0, .03),
                       'direction': (0, 2*np.pi),
                       'heading': (0, 2*np.pi),
                       'heading_diff': (0, 0.261799),
                       'del_rot_error': (0, 15000),
                       'del_rot_cam_vec': (-0.025, 0.025)}

    # Setup a queue for caching the historical data received so we can plot history of samples up to
    # some N
    data_history = deque([FicTracState() for i in range(num_history)], maxlen=num_history)

    plot_data = np.zeros((num_history, num_channels))

    # We want to create a subplot for each channel
    axes = []
    backgrounds = []
    point_sets = []
    for chn in range(1, num_channels + 1):
        field_name = fictrac_state_fields[chn-1]
        ax = fig.add_subplot(num_channels, 1, chn)
        ax.set_title(field_name)
        backgrounds.append(fig.canvas.copy_from_bbox(ax.bbox))  # cache the background
        ax.axis([0, num_history, field_ax_limits[field_name][0], field_ax_limits[field_name][1]])
        axes.append(ax)
        point_sets.append(ax.plot(np.arange(num_history), plot_data)[0])  # init plot content

    plt.show()
    plt.draw()
    fig.canvas.start_event_loop(0.001)  # otherwise plot freezes after 3-4 iterations

    RUN = True
    data = fictrac.FicTracState.from_buffer(shmem)
    first_frame_count = data.frame_cnt
    old_frame_count = data.frame_cnt
    while flyvr_state.is_running_well():
        new_frame_count = data.frame_cnt

        if old_frame_count != new_frame_count:

            # Copy the current state.
            data_copy = FicTracState()
            ctypes.pointer(data_copy)[0] = data

            # Append to the history
            data_history.append(data_copy)

            # Turned the queued chunks into a flat array
            sample_i = 0
            last_d = data_history[0]
            for d in data_history:
                chan_i = 0
                for field in fictrac_state_fields:
                    if field.endswith('_diff'):
                        real_field = field.replace('_diff', '')

                        if real_field in ['heading', 'direction']:
                            plot_data[sample_i, chan_i] = abs(angle_diff(getattr(d, real_field), getattr(last_d, real_field)))
                        else:
                            plot_data[sample_i, chan_i] = getattr(d, real_field) - getattr(last_d, real_field)
                    elif field.endswith('vec'):
                        plot_data[sample_i, chan_i] = getattr(d, field)[1]
                    else:
                        plot_data[sample_i,chan_i] = getattr(d, field)
                    chan_i = chan_i + 1
                last_d = d
                sample_i = sample_i + 1

            for chn in range(num_channels):
                fig.canvas.restore_region(backgrounds[chn])         # restore background
                point_sets[chn].set_data(np.arange(num_history), plot_data[:,chn])
                axes[chn].draw_artist(point_sets[chn])              # redraw just the points
                #fig.canvas.blit(axes[chn].bbox)                    # fill in the axes rectangle

            fig.canvas.draw()
            fig.canvas.flush_events()

    # clean up
    plt.close(fig)
