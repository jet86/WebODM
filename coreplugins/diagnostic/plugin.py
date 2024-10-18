from app.plugins import PluginBase, Menu, MountPoint
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _

import json, shutil, psutil

def get_memory_stats_old():
    """
    Get node total memory and memory usage (Linux only)
    https://stackoverflow.com/questions/17718449/determine-free-ram-in-python
    """
    try:
        with open('/proc/meminfo', 'r') as mem:
            ret = {}
            tmp = 0
            for i in mem:
                sline = i.split()
                if str(sline[0]) == 'MemTotal:':
                    ret['total'] = int(sline[1])
                elif str(sline[0]) in ('MemFree:', 'Buffers:', 'Cached:'):
                    tmp += int(sline[1])
            ret['free'] = tmp
            ret['used'] = int(ret['total']) - int(ret['free'])

            ret['total'] *= 1024
            ret['free'] *= 1024
            ret['used'] *= 1024
        return ret
    except:
        return {}


class Plugin(PluginBase):
    def main_menu(self):
        return [Menu(_("Diagnostic"), self.public_url(""), "fa fa-chart-pie fa-fw")]

    def app_mount_points(self):
        @login_required
        def diagnostic(request):
            # Disk space old
            total_disk_space_old, used_disk_space_old, free_disk_space_old = shutil.disk_usage('./')
            
            # Disk space
            disk_usage = psutil.disk_usage('./')
            
            # Memory
            memory_usage = psutil.virtual_memory()
            swap_usage = psutil.swap_memory()

            template_args = {
                'title': 'Diagnostic',
                # Disk space old
                'total_disk_space_old': total_disk_space_old,
                'used_disk_space_old': used_disk_space_old,
                'free_disk_space_old': free_disk_space_old,
                # Disk space
                'total_disk_space': disk_usage.total,
                'used_disk_space': disk_usage.used,
                'free_disk_space': disk_usage.free,
                # Memory
                'total_memory': memory_usage.total,
                'used_memory': memory_usage.total - memory_usage.available,
                'free_memory': memory_usage.available,
                'total_swap': swap_usage.total,
                'used_swap': swap_usage.used,
                'free_swap': swap_usage.free
            }

            # Memory (Linux only)
            memory_stats_old = get_memory_stats_old()
            if 'free' in memory_stats_old:
                template_args['free_memory_old'] = memory_stats_old['free']
                template_args['used_memory_old'] = memory_stats_old['used']
                template_args['total_memory_old'] = memory_stats_old['total']

            return render(request, self.template_path("diagnostic.html"), template_args)

        return [
            MountPoint('$', diagnostic)
        ]


