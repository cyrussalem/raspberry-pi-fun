import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { environment } from '../environments/environment';

@Component({
  selector: 'app-root',
  imports: [MatButtonModule, MatIconModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  readonly streamUrl = `${environment.apiBaseUrl}/api/video/stream`;

  readonly buttons = [
    { label: 'Snapshot', icon: 'photo_camera' },
    { label: 'Record', icon: 'videocam' },
    { label: 'Settings', icon: 'settings' },
    { label: 'Detect', icon: 'face' },
    { label: 'Fullscreen', icon: 'fullscreen' },
    { label: 'Info', icon: 'info' },
  ];
}
