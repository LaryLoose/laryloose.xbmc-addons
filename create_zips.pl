#!/usr/bin/perl

use strict;
use File::Basename;

my $sourcepath = '.';
my $destpath = "$sourcepath/zips";

sub is_empty($)
{
    my $var = shift;
    return (!defined($var) || ($var eq ''));
}

sub get_addon_folder
{
    my $actfolder = shift;
    if (is_empty($actfolder)) { print "get_addon_folder(): actfolder is empty\n"; exit 1; }
    return sort split("\n", `ls -d $actfolder/*.*.*`);
}

sub get_addon_details
{
    my $xml = shift;
    if (is_empty($xml)) { print "get_addon_details(): addonxml is empty\n"; exit 2; }
    if (!open FILE, "<$xml") { print "cannot open xml file $xml\n"; exit 2; }

    my ($id, $version);

    while (<FILE>)
    {
        my $line = $_;
        if ($line =~ m/(<addon.*?>)/i)
        {
	    $line = $1;
	    if ($line =~ m/id="(.*?)"/i) { $id = $1; }
	    if ($line =~ m/version="(.*?)"/i) { $version = $1; }
	    last;
	}
    }
    close FILE;
    return ($id, $version);
}

foreach my $folder (get_addon_folder($sourcepath))
{
    if ($folder =~ m/\/(plugin|repository)[^\/]*/i)
    {
	my ($id, $version) =  get_addon_details("$folder/addon.xml");
	my $actzipfolder = "$destpath/$id";
	if ((!-e $actzipfolder) && !mkdir($actzipfolder)) { print "could not create dir $actzipfolder"; exit 3; }
	my $zipfile = "$actzipfolder/$id-$version.zip";
	my $changefile = "$folder/changelog.txt";
	my $iconfile = "$folder/icon.png";

	if (!-e $zipfile) { print "creating file $zipfile\n"; `zip -r $zipfile $folder`; }
	if (-e $changefile) { print "copy file $changefile\n"; `cp $changefile $actzipfolder/changelog.txt`; }
	if (-e $iconfile) { print "copy file $iconfile\n"; `cp $iconfile $actzipfolder/icon.png`; }
    }
}