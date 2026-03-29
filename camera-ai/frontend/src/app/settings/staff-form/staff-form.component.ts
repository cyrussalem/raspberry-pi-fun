import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatToolbarModule } from '@angular/material/toolbar';
import { StaffService, StaffRecord } from '../../services/staff.service';
import { HttpErrorResponse } from '@angular/common/http';

@Component({
  selector: 'app-staff-form',
  standalone: true,
  imports: [
    FormsModule,
    MatButtonModule,
    MatCardModule,
    MatDialogModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatSnackBarModule,
    MatToolbarModule,
  ],
  templateUrl: './staff-form.component.html',
  styleUrl: './staff-form.component.css',
})
export class StaffFormComponent implements OnInit {
  isEditMode = false;
  staffId: string | null = null;
  staffName = '';
  photos: string[] = [];
  selectedFile: File | null = null;
  error: string | null = null;
  isSubmitting = false;
  isLoading = false;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private staffService: StaffService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    const id = this.route.snapshot.paramMap.get('id');
    if (id && id !== 'new') {
      this.isEditMode = true;
      this.staffId = id;
      this.loadStaff();
    }
  }

  goBack(): void {
    this.router.navigate(['/settings']);
  }

  get pageTitle(): string {
    return this.isEditMode ? 'Edit Staff' : 'Add New Staff';
  }

  get isAddValid(): boolean {
    return this.staffName.trim().length > 0 && this.selectedFile !== null;
  }

  // --- Add Mode ---

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.selectedFile = input.files[0];
    }
  }

  submitNew(): void {
    if (!this.isAddValid || this.isSubmitting) return;

    this.error = null;
    this.isSubmitting = true;

    this.staffService.registerStaff(this.staffName.trim()).subscribe({
      next: (response) => {
        const newId = response.data?.id;
        if (newId && this.selectedFile) {
          this.uploadPhotoForStaff(newId);
        } else {
          this.onAddSuccess();
        }
      },
      error: (err: HttpErrorResponse) => {
        this.error = err.error?.message || 'Failed to register staff member.';
        this.isSubmitting = false;
      },
    });
  }

  private uploadPhotoForStaff(staffId: string): void {
    this.staffService.uploadPhoto(staffId, this.selectedFile!).subscribe({
      next: () => {
        this.onAddSuccess();
      },
      error: (err: HttpErrorResponse) => {
        // Staff was registered but photo failed — still navigate back
        this.snackBar.open(
          err.error?.message || 'Staff registered but photo upload failed.',
          'OK',
          { duration: 5000, panelClass: ['snackbar-error'] }
        );
        this.isSubmitting = false;
        this.router.navigate(['/settings']);
      },
    });
  }

  private onAddSuccess(): void {
    this.snackBar.open('Staff member added successfully.', 'OK', {
      duration: 4000,
      panelClass: ['snackbar-success'],
    });
    this.isSubmitting = false;
    this.router.navigate(['/settings']);
  }

  // --- Edit Mode ---

  loadStaff(): void {
    this.isLoading = true;
    this.staffService.getStaff(this.staffId!).subscribe({
      next: (response) => {
        const data = response.data as StaffRecord;
        this.staffName = data.name;
        this.photos = data.photos;
        this.isLoading = false;
      },
      error: () => {
        this.error = 'Failed to load staff member.';
        this.isLoading = false;
      },
    });
  }

  getPhotoUrl(photoPath: string): string {
    return this.staffService.getPhotoUrl(photoPath);
  }

  getPhotoFilename(photoPath: string): string {
    return photoPath.split('/').pop() || photoPath;
  }

  uploadNewPhoto(): void {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = (event: Event) => {
      const target = event.target as HTMLInputElement;
      if (target.files && target.files.length > 0) {
        this.isSubmitting = true;
        this.error = null;
        this.staffService
          .uploadPhoto(this.staffId!, target.files[0])
          .subscribe({
            next: () => {
              this.snackBar.open('Photo added.', 'OK', {
                duration: 3000,
                panelClass: ['snackbar-success'],
              });
              this.isSubmitting = false;
              this.loadStaff();
            },
            error: (err: HttpErrorResponse) => {
              this.error =
                err.error?.message || 'Failed to upload photo.';
              this.isSubmitting = false;
            },
          });
      }
    };
    input.click();
  }

  deletePhoto(photoPath: string): void {
    this.staffService.deletePhoto(this.staffId!, photoPath).subscribe({
      next: () => {
        this.snackBar.open('Photo removed.', 'OK', {
          duration: 3000,
          panelClass: ['snackbar-success'],
        });
        this.loadStaff();
      },
      error: (err: HttpErrorResponse) => {
        this.error = err.error?.message || 'Failed to delete photo.';
      },
    });
  }

  deleteStaff(): void {
    if (!confirm(`Delete ${this.staffName}? This will remove all photos.`)) {
      return;
    }

    this.staffService.deleteStaff(this.staffId!).subscribe({
      next: (response) => {
        this.snackBar.open(response.message, 'OK', {
          duration: 4000,
          panelClass: ['snackbar-success'],
        });
        this.router.navigate(['/settings']);
      },
      error: (err: HttpErrorResponse) => {
        this.error = err.error?.message || 'Failed to delete staff member.';
      },
    });
  }
}
