import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { environment } from '../environments/environment';
import { KeypadDialogComponent } from './dialogs/keypad-dialog/keypad-dialog.component';
import { UpdateCodeDialogComponent } from './dialogs/update-code-dialog/update-code-dialog.component';

@Component({
  selector: 'app-root',
  imports: [MatButtonModule, MatIconModule, MatDialogModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  readonly streamUrl = `${environment.apiBaseUrl}/api/video/stream`;

  readonly buttons = [
    { label: 'Door Pin', icon: 'dialpad' },
    { label: 'Settings', icon: 'settings' },
    { label: 'Snapshot', icon: 'photo_camera' },
    { label: 'Record', icon: 'videocam' },
    { label: 'Fullscreen', icon: 'fullscreen' },
    { label: 'Info', icon: 'info' },
  ];

  constructor(private dialog: MatDialog) {}

  onButtonClick(label: string): void {
    switch (label) {
      case 'Door Pin':
        this.dialog.open(KeypadDialogComponent, {
          width: '520px',
          panelClass: 'dark-dialog',
        });
        break;
      case 'Settings':
        this.dialog.open(UpdateCodeDialogComponent, {
          width: '360px',
          panelClass: 'dark-dialog',
        });
        break;
    }
  }
}
